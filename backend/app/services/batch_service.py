"""
Service layer for batch operations
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import database as db_models
from ooj_client import entities


def create_batch(
    db: Session,
    batch_id: str,
    actor_id: str,
    item_id: str,
    quantity: Optional[entities.Quantity] = None,
    status: str = "active",
    production_date: Optional[str] = None,
    **kwargs
) -> db_models.Batch:
    """Create a new batch with OOJ compliance"""
    now = datetime.utcnow().isoformat() + "Z"
    
    batch = entities.Batch(
        id=batch_id,
        actor_id=actor_id,
        item_id=item_id,
        quantity=quantity,
        status=status,
        production_date=production_date,
        created_at=now,
        updated_at=now,
        **kwargs
    )
    
    db_batch = db_models.Batch(
        id=batch_id,
        actor_id=actor_id,
        item_id=item_id,
        status=status,
        production_date=production_date,
        jsonb_doc=batch.to_dict()
    )
    
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    
    return db_batch


def get_batches_by_actor(
    db: Session,
    actor_id: str,
    status: Optional[str] = None,
    item_id: Optional[str] = None
) -> List[db_models.Batch]:
    """Get all batches for an actor with optional filters"""
    query = db.query(db_models.Batch).filter(db_models.Batch.actor_id == actor_id)
    
    if status:
        query = query.filter(db_models.Batch.status == status)
    if item_id:
        query = query.filter(db_models.Batch.item_id == item_id)
    
    return query.all()


def get_batch(db: Session, actor_id: str, batch_id: str) -> Optional[db_models.Batch]:
    """Get a specific batch"""
    return db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.id == batch_id
    ).first()


def update_batch_status(
    db: Session,
    actor_id: str,
    batch_id: str,
    new_status: str
) -> Optional[db_models.Batch]:
    """Update batch status"""
    batch = get_batch(db, actor_id, batch_id)
    if not batch:
        return None
    
    batch.status = new_status
    doc = batch.jsonb_doc
    doc['status'] = new_status
    doc['updated_at'] = datetime.utcnow().isoformat() + "Z"
    batch.jsonb_doc = doc
    
    db.commit()
    db.refresh(batch)
    
    return batch
