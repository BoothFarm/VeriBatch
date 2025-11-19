"""
API routes for actors
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities

router = APIRouter(prefix="/actors", tags=["actors"])


@router.post("", response_model=dict)
def create_actor(actor_data: dict, db: Session = Depends(get_db)):
    """Create a new actor"""
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
        
        # Check if actor already exists
        existing = db.query(db_models.Actor).filter(
            db_models.Actor.id == actor_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Actor already exists")
        
        db_actor = db_models.Actor(
            id=actor_data["id"],
            name=actor_data["name"],
            kind=actor_data.get("kind"),
            jsonb_doc=actor_data
        )
        
        db.add(db_actor)
        db.commit()
        db.refresh(db_actor)
        
        return db_actor.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")


@router.get("/{actor_id}", response_model=dict)
def get_actor(actor_id: str, db: Session = Depends(get_db)):
    """Get an actor by ID"""
    actor = db.query(db_models.Actor).filter(db_models.Actor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    return actor.jsonb_doc


@router.get("", response_model=List[dict])
def list_actors(db: Session = Depends(get_db)):
    """List all actors"""
    actors = db.query(db_models.Actor).all()
    return [actor.jsonb_doc for actor in actors]
