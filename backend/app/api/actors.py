"""
API routes for actors
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities
from app.dependencies import get_current_active_user, get_current_active_user_and_owned_actor # New import

router = APIRouter(prefix="/actors", tags=["actors"])


@router.post("", response_model=dict)
def create_actor(
    actor_data: dict, 
    current_user: Annotated[db_models.User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """Create a new actor (Protected)"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in actor_data:
            actor_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in actor_data:
            actor_data["type"] = "actor"
        if "created_at" not in actor_data:
            actor_data["created_at"] = now
        actor_data["updated_at"] = now
        
        # Check if actor already exists for this user
        existing = db.query(db_models.Actor).filter(
            db_models.Actor.id == actor_data["id"],
            db_models.Actor.owner_id == current_user.pk
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Actor with this ID already exists for this user")
        
        db_actor = db_models.Actor(
            id=actor_data["id"],
            name=actor_data["name"],
            kind=actor_data.get("kind"),
            owner_id=current_user.pk, # Associate with current user
            jsonb_doc=actor_data
        )
        
        db.add(db_actor)
        db.commit()
        db.refresh(db_actor)
        
        return db_actor.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {e}")


@router.get("/{actor_id}", response_model=dict)
def get_actor(
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)]
):
    """Get an actor by ID (Protected, must be owned by user)"""
    return actor.jsonb_doc


@router.get("", response_model=List[dict])
def list_actors(
    current_user: Annotated[db_models.User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """List all actors owned by the current user (Protected)"""
    actors = db.query(db_models.Actor).filter(db_models.Actor.owner_id == current_user.pk).all()
    return [actor.jsonb_doc for actor in actors]
