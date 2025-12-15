"""
API routes for processes (recipes/SOPs)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities
from app.dependencies import get_current_active_user_and_owned_actor # Add this import

router = APIRouter(prefix="/actors/{actor_id}/processes", tags=["processes"])


@router.post("", response_model=dict)
def create_process(
    process_data: dict, 
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Create a new process/recipe (Protected)"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in process_data:
            process_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in process_data:
            process_data["type"] = "process"
        process_data["actor_id"] = actor.id
        if "created_at" not in process_data:
            process_data["created_at"] = now
        process_data["updated_at"] = now
        
        # Check if process already exists
        existing = db.query(db_models.Process).filter(
            db_models.Process.actor_id == actor.id,
            db_models.Process.id == process_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Process already exists for this actor")
        
        db_process = db_models.Process(
            id=process_data["id"],
            actor_id=actor.id,
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {e}")


@router.get("", response_model=List[dict])
def list_processes(
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)],
    kind: Optional[str] = None,
):
    """List all processes for an actor (Protected)"""
    query = db.query(db_models.Process).filter(db_models.Process.actor_id == actor.id)
    
    if kind:
        query = query.filter(db_models.Process.kind == kind)
    
    processes = query.all()
    return [process.jsonb_doc for process in processes]


@router.get("/{process_id}", response_model=dict)
def get_process(
    process_id: str, 
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Get a specific process (Protected)"""
    process = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor.id,
        db_models.Process.id == process_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")
    
    return process.jsonb_doc


@router.put("/{process_id}", response_model=dict)
def update_process(
    process_id: str,
    process_data: dict,
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Update a process (Protected)"""
    process = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor.id,
        db_models.Process.id == process_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")
    
    now = datetime.utcnow().isoformat() + "Z"
    process_data["actor_id"] = actor.id
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


@router.delete("/{process_id}", response_model=dict)
def delete_process(
    process_id: str, 
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Delete a process (Protected)"""
    process = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor.id,
        db_models.Process.id == process_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")
    
    db.delete(process)
    db.commit()
    
    return {"message": "Process deleted successfully"}
