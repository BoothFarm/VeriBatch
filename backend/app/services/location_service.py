"""
Service layer for location operations
"""
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.models import database as db_models
from ooj_client import entities

def get_location(db: Session, actor_id: str, location_id: str) -> Optional[db_models.Location]:
    """Get a specific location"""
    return db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor_id,
        db_models.Location.id == location_id
    ).first()

def create_location(
    db: Session,
    actor_id: str,
    location_id: str,
    name: str,
    kind: str = "field",
    description: Optional[str] = None,
    address: Optional[Dict] = None,
    coordinates: Optional[Dict] = None
) -> db_models.Location:
    """Create a new location"""
    now = datetime.utcnow().isoformat() + "Z"
    
    location_data = {
        "schema": entities.SCHEMA_VERSION,
        "type": "location",
        "id": location_id,
        "actor_id": actor_id,
        "name": name,
        "kind": kind,
        "created_at": now,
        "updated_at": now
    }
    
    if description:
        location_data["description"] = description
    if address:
        location_data["address"] = address
    if coordinates:
        location_data["coordinates"] = coordinates
        
    db_location = db_models.Location(
        id=location_id,
        actor_id=actor_id,
        name=name,
        kind=kind,
        jsonb_doc=location_data
    )
    
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return db_location

def update_location(
    db: Session,
    actor_id: str,
    location_id: str,
    data: dict
) -> Optional[db_models.Location]:
    """Update an existing location"""
    location = get_location(db, actor_id, location_id)
    if not location:
        return None
        
    # Update fields
    if "name" in data:
        location.name = data["name"]
        
    if "kind" in data:
        location.kind = data["kind"]
        
    # Update JSON doc
    doc = location.jsonb_doc.copy()
    
    for key, value in data.items():
        if value is None:
            doc.pop(key, None)
        else:
            doc[key] = value
        
    doc["updated_at"] = datetime.utcnow().isoformat() + "Z"
    location.jsonb_doc = doc
    
    db.commit()
    db.refresh(location)
    
    return location
