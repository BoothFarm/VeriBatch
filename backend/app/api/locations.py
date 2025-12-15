"""
API routes for locations (Level 3)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities
from app.dependencies import get_current_active_user_and_owned_actor # Add this import

router = APIRouter(prefix="/actors/{actor_id}/locations", tags=["locations"])


@router.post("", response_model=dict)
def create_location(
    location_data: dict, 
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Create a new location (Protected)"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in location_data:
            location_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in location_data:
            location_data["type"] = "location"
        location_data["actor_id"] = actor.id
        if "created_at" not in location_data:
            location_data["created_at"] = now
        location_data["updated_at"] = now
        
        # Check if location already exists
        existing = db.query(db_models.Location).filter(
            db_models.Location.actor_id == actor.id,
            db_models.Location.id == location_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location already exists for this actor")
        
        db_location = db_models.Location(
            id=location_data["id"],
            actor_id=actor.id,
            name=location_data["name"],
            kind=location_data.get("kind"),
            jsonb_doc=location_data
        )
        
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        
        return db_location.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {e}")


@router.get("", response_model=List[dict])
def list_locations(
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)],
    kind: Optional[str] = None,
):
    """List all locations for an actor (Protected)"""
    query = db.query(db_models.Location).filter(db_models.Location.actor_id == actor.id)
    
    if kind:
        query = query.filter(db_models.Location.kind == kind)
    
    locations = query.all()
    return [location.jsonb_doc for location in locations]


@router.get("/{location_id}", response_model=dict)
def get_location(
    location_id: str, 
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Get a specific location (Protected)"""
    location = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor.id,
        db_models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    
    return location.jsonb_doc

@router.put("/{location_id}", response_model=dict)
def update_location(
    location_id: str,
    location_data: dict,
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Update a location (Protected)"""
    location = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor.id,
        db_models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    
    now = datetime.utcnow().isoformat() + "Z"
    location_data["actor_id"] = actor.id
    location_data["id"] = location_id
    location_data["updated_at"] = now
    
    # Update indexed fields (name, kind)
    location.name = location_data.get("name", location.name)
    location.kind = location_data.get("kind", location.kind)
    location.jsonb_doc = location_data
    
    db.commit()
    db.refresh(location)
    
    return location.jsonb_doc


@router.delete("/{location_id}", response_model=dict)
def delete_location(
    location_id: str, 
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Delete a location (Protected)"""
    location = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor.id,
        db_models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    
    db.delete(location)
    db.commit()
    
    return {"message": "Location deleted successfully"}
