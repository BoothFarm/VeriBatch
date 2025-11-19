"""
API routes for locations (Level 3)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities

router = APIRouter(prefix="/actors/{actor_id}/locations", tags=["locations"])


@router.post("", response_model=dict)
def create_location(actor_id: str, location_data: dict, db: Session = Depends(get_db)):
    """Create a new location"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in location_data:
            location_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in location_data:
            location_data["type"] = "location"
        location_data["actor_id"] = actor_id
        if "created_at" not in location_data:
            location_data["created_at"] = now
        location_data["updated_at"] = now
        
        # Check if location already exists
        existing = db.query(db_models.Location).filter(
            db_models.Location.actor_id == actor_id,
            db_models.Location.id == location_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Location already exists")
        
        db_location = db_models.Location(
            id=location_data["id"],
            actor_id=actor_id,
            name=location_data["name"],
            kind=location_data.get("kind"),
            jsonb_doc=location_data
        )
        
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        
        return db_location.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")


@router.get("", response_model=List[dict])
def list_locations(
    actor_id: str,
    kind: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all locations for an actor"""
    query = db.query(db_models.Location).filter(db_models.Location.actor_id == actor_id)
    
    if kind:
        query = query.filter(db_models.Location.kind == kind)
    
    locations = query.all()
    return [location.jsonb_doc for location in locations]


@router.get("/{location_id}", response_model=dict)
def get_location(actor_id: str, location_id: str, db: Session = Depends(get_db)):
    """Get a specific location"""
    location = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor_id,
        db_models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return location.jsonb_doc
