"""
API routes for events
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities

router = APIRouter(prefix="/actors/{actor_id}/events", tags=["events"])


@router.post("", response_model=dict)
def create_event(actor_id: str, event_data: dict, db: Session = Depends(get_db)):
    """Create a new event"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in event_data:
            event_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in event_data:
            event_data["type"] = "event"
        event_data["actor_id"] = actor_id
        if "created_at" not in event_data:
            event_data["created_at"] = now
        event_data["updated_at"] = now
        
        # Check if event already exists
        existing = db.query(db_models.Event).filter(
            db_models.Event.actor_id == actor_id,
            db_models.Event.id == event_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Event already exists")
        
        db_event = db_models.Event(
            id=event_data["id"],
            actor_id=actor_id,
            event_type=event_data["event_type"],
            timestamp=event_data["timestamp"],
            jsonb_doc=event_data
        )
        
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        return db_event.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")


@router.get("", response_model=List[dict])
def list_events(
    actor_id: str,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all events for an actor"""
    query = db.query(db_models.Event).filter(db_models.Event.actor_id == actor_id)
    
    if event_type:
        query = query.filter(db_models.Event.event_type == event_type)
    
    events = query.order_by(db_models.Event.timestamp.desc()).all()
    return [event.jsonb_doc for event in events]


@router.get("/{event_id}", response_model=dict)
def get_event(actor_id: str, event_id: str, db: Session = Depends(get_db)):
    """Get a specific event"""
    event = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id,
        db_models.Event.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event.jsonb_doc
