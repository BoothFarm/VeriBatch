"""
API routes for processes (recipes/SOPs)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities

router = APIRouter(prefix="/actors/{actor_id}/processes", tags=["processes"])


@router.post("", response_model=dict)
def create_process(actor_id: str, process_data: dict, db: Session = Depends(get_db)):
    """Create a new process/recipe"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in process_data:
            process_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in process_data:
            process_data["type"] = "process"
        process_data["actor_id"] = actor_id
        if "created_at" not in process_data:
            process_data["created_at"] = now
        process_data["updated_at"] = now
        
        # Check if process already exists
        existing = db.query(db_models.Process).filter(
            db_models.Process.actor_id == actor_id,
            db_models.Process.id == process_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Process already exists")
        
        db_process = db_models.Process(
            id=process_data["id"],
            actor_id=actor_id,
            name=process_data["name"],
            kind=process_data.get("kind"),
            version=process_data.get("version"),
            jsonb_doc=process_data
        )
        
        db.add(db_process)
        db.commit()
        db.refresh(db_process)
        
        return db_process.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")


@router.get("", response_model=List[dict])
def list_processes(
    actor_id: str,
    kind: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all processes for an actor"""
    query = db.query(db_models.Process).filter(db_models.Process.actor_id == actor_id)
    
    if kind:
        query = query.filter(db_models.Process.kind == kind)
    
    processes = query.all()
    return [process.jsonb_doc for process in processes]


@router.get("/{process_id}", response_model=dict)
def get_process(actor_id: str, process_id: str, db: Session = Depends(get_db)):
    """Get a specific process"""
    process = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor_id,
        db_models.Process.id == process_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    return process.jsonb_doc


@router.put("/{process_id}", response_model=dict)
def update_process(
    actor_id: str,
    process_id: str,
    process_data: dict,
    db: Session = Depends(get_db)
):
    """Update a process"""
    process = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor_id,
        db_models.Process.id == process_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    now = datetime.utcnow().isoformat() + "Z"
    process_data["actor_id"] = actor_id
    process_data["id"] = process_id
    process_data["updated_at"] = now
    
    # Update indexed fields
    process.name = process_data.get("name", process.name)
    process.kind = process_data.get("kind", process.kind)
    process.version = process_data.get("version", process.version)
    process.jsonb_doc = process_data
    
    db.commit()
    db.refresh(process)
    
    return process.jsonb_doc
