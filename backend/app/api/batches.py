"""
API routes for batches
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from app.services import batch_service
from ooj_client import entities

router = APIRouter(prefix="/actors/{actor_id}/batches", tags=["batches"])


@router.post("", response_model=dict)
def create_batch(actor_id: str, batch_data: dict, db: Session = Depends(get_db)):
    """Create a new batch"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in batch_data:
            batch_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in batch_data:
            batch_data["type"] = "batch"
        batch_data["actor_id"] = actor_id
        if "created_at" not in batch_data:
            batch_data["created_at"] = now
        batch_data["updated_at"] = now
        if "status" not in batch_data:
            batch_data["status"] = "active"
        
        # Check if batch already exists
        existing = db.query(db_models.Batch).filter(
            db_models.Batch.actor_id == actor_id,
            db_models.Batch.id == batch_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Batch already exists")
        
        db_batch = db_models.Batch(
            id=batch_data["id"],
            actor_id=actor_id,
            item_id=batch_data["item_id"],
            status=batch_data.get("status", "active"),
            production_date=batch_data.get("production_date"),
            expiration_date=batch_data.get("expiration_date"),
            jsonb_doc=batch_data
        )
        
        db.add(db_batch)
        db.commit()
        db.refresh(db_batch)
        
        return db_batch.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")


@router.get("", response_model=List[dict])
def list_batches(
    actor_id: str,
    status: Optional[str] = None,
    item_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all batches for an actor"""
    query = db.query(db_models.Batch).filter(db_models.Batch.actor_id == actor_id)
    
    if status:
        query = query.filter(db_models.Batch.status == status)
    if item_id:
        query = query.filter(db_models.Batch.item_id == item_id)
    
    batches = query.order_by(db_models.Batch.production_date.desc()).all()
    return [batch.jsonb_doc for batch in batches]


@router.get("/{batch_id}", response_model=dict)
def get_batch(actor_id: str, batch_id: str, db: Session = Depends(get_db)):
    """Get a specific batch"""
    batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.id == batch_id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return batch.jsonb_doc


@router.patch("/{batch_id}/status", response_model=dict)
def update_batch_status(
    actor_id: str,
    batch_id: str,
    status_data: dict,
    db: Session = Depends(get_db)
):
    """Update batch status"""
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status field required")
    
    batch = batch_service.update_batch_status(db, actor_id, batch_id, new_status)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return batch.jsonb_doc
