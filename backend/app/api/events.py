"""
API routes for events
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities
from app.dependencies import get_current_active_user_and_owned_actor # Add this import
from app.services import event_service

router = APIRouter(prefix="/actors/{actor_id}/events", tags=["events"])


@router.post("", response_model=dict)
def create_event(
    event_data: dict, 
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Create a new event (Protected)"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in event_data:
            event_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in event_data:
            event_data["type"] = "event"
        event_data["actor_id"] = actor.id
        if "created_at" not in event_data:
            event_data["created_at"] = now
        event_data["updated_at"] = now
        
        # Check if event already exists
        existing = db.query(db_models.Event).filter(
            db_models.Event.actor_id == actor.id,
            db_models.Event.id == event_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event already exists for this actor")
        
        db_event = db_models.Event(
            id=event_data["id"],
            actor_id=actor.id,
            event_type=event_data["event_type"],
            timestamp=event_data["timestamp"],
            jsonb_doc=event_data
        )
        
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        return db_event.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {e}")


@router.get("", response_model=List[dict])
def list_events(
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)],
    event_type: Optional[str] = None,
):
    """List all events for an actor (Protected)"""
    query = db.query(db_models.Event).filter(db_models.Event.actor_id == actor.id)
    
    if event_type:
        query = query.filter(db_models.Event.event_type == event_type)
    
    events = query.order_by(db_models.Event.timestamp.desc()).all()
    return [event.jsonb_doc for event in events]


@router.get("/{event_id}", response_model=dict)
def get_event(
    event_id: str, 
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Get a specific event (Protected)"""
    event = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor.id,
        db_models.Event.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    return event.jsonb_doc


@router.put("/{event_id}", response_model=dict)
def update_event(
    event_id: str,
    event_data: dict,
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Update an event (Protected)"""
    event = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor.id,
        db_models.Event.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    # Simple update for now, can extend to use event_service
    event.jsonb_doc = event_data # Overwrite entire doc
    event.timestamp = event_data.get("timestamp", event.timestamp)
    
    db.commit()
    db.refresh(event)
    
    return event.jsonb_doc


@router.delete("/{event_id}", response_model=dict)
def delete_event(
    event_id: str, 
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Delete an event (Protected)"""
    event = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor.id,
        db_models.Event.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    db.delete(event)
    db.commit()
    
    return {"message": "Event deleted successfully"}
