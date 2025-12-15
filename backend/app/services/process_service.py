"""
Service layer for process operations
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import database as db_models
from ooj_client import entities

def get_process(db: Session, actor_id: str, process_id: str) -> Optional[db_models.Process]:
    """Get a specific process"""
    return db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor_id,
        db_models.Process.id == process_id
    ).first()

def create_process(
    db: Session,
    actor_id: str,
    process_id: str,
    name: str,
    kind: str = "processing",
    description: Optional[str] = None,
    version: Optional[str] = None,
    steps: Optional[List[str]] = None
) -> db_models.Process:
    """Create a new process"""
    now = datetime.utcnow().isoformat() + "Z"
    
    process_data = {
        "schema": entities.SCHEMA_VERSION,
        "type": "process",
        "id": process_id,
        "actor_id": actor_id,
        "name": name,
        "kind": kind,
        "created_at": now,
        "updated_at": now
    }
    
    if description:
        process_data["description"] = description
    if version:
        process_data["version"] = version
    if steps:
        process_data["steps"] = steps
        
    db_process = db_models.Process(
        id=process_id,
        actor_id=actor_id,
        name=name,
        kind=kind,
        version=version,
        jsonb_doc=process_data
    )
    
    db.add(db_process)
    db.commit()
    db.refresh(db_process)
    
    return db_process

def update_process(
    db: Session,
    actor_id: str,
    process_id: str,
    data: dict
) -> Optional[db_models.Process]:
    """Update an existing process"""
    process = get_process(db, actor_id, process_id)
    if not process:
        return None
        
    # Update fields
    if "name" in data:
        process.name = data["name"]
        
    if "kind" in data:
        process.kind = data["kind"]
        
    if "version" in data:
        process.version = data["version"]
        
    # Update JSON doc
    doc = process.jsonb_doc.copy()
    
    for key, value in data.items():
        if value is None:
            doc.pop(key, None)
        else:
            doc[key] = value
        
    doc["updated_at"] = datetime.utcnow().isoformat() + "Z"
    process.jsonb_doc = doc
    
    db.commit()
    db.refresh(process)
    
    return process
