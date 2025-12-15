"""
Service layer for batch operations
"""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models import database as db_models
from ooj_client import entities
from app.services.validation import validate_batch_quantity, validate_date_order, ValidationError


def create_batch(
    db: Session,
    batch_id: str,
    actor_id: str,
    item_id: str,
    quantity: Optional[entities.Quantity] = None,
    status: str = "active",
    production_date: Optional[str] = None,
    expiration_date: Optional[str] = None,
    **kwargs
) -> db_models.Batch:
    """Create a new batch with OOJ compliance and validation"""
    # Validate quantity if provided
    if quantity:
        qty_dict = {"amount": quantity.amount, "unit": quantity.unit}
        validate_batch_quantity(qty_dict)
    
    # Validate dates
    validate_date_order(production_date, expiration_date)
    
    now = datetime.utcnow().isoformat() + "Z"
    
    batch = entities.Batch(
        id=batch_id,
        actor_id=actor_id,
        item_id=item_id,
        quantity=quantity,
        status=status,
        production_date=production_date,
        expiration_date=expiration_date,
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
        expiration_date=expiration_date,
        jsonb_doc=batch.to_dict()
    )
    
    if "is_mock_recall" in kwargs:
        db_batch.is_mock_recall = kwargs["is_mock_recall"]
    
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    
    return db_batch


def get_batches_by_actor(
    db: Session,
    actor_id: str,
    status: Optional[str] = None,
    item_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[db_models.Batch], int]:
    """Get batches with filters and pagination"""
    query = db.query(db_models.Batch).filter(db_models.Batch.actor_id == actor_id)
    
    if status:
        query = query.filter(db_models.Batch.status == status)
    if item_id:
        query = query.filter(db_models.Batch.item_id == item_id)
        
    total = query.count()
    items = query.order_by(db_models.Batch.production_date.desc()).offset(skip).limit(limit).all()
    
    return items, total


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


def update_batch_details(
    db: Session,
    actor_id: str,
    batch_id: str,
    data: dict
) -> db_models.Batch:
    """Update batch details (quantity, dates, notes, etc.)"""
    batch = get_batch(db, actor_id, batch_id)
    if not batch:
        return None
    
    doc = batch.jsonb_doc.copy()
    
    # Update fields if present in data
    if "production_date" in data:
        batch.production_date = data["production_date"]
        doc["production_date"] = data["production_date"]
        
    if "expiration_date" in data:
        batch.expiration_date = data["expiration_date"]
        doc["expiration_date"] = data["expiration_date"]
        
    if "status" in data:
        batch.status = data["status"]
        doc["status"] = data["status"]
        
    # JSON-only fields
    if "quantity" in data:
        doc["quantity"] = data["quantity"]
        
    if "origin_kind" in data:
        doc["origin_kind"] = data["origin_kind"]
        
    if "notes" in data:
        doc["notes"] = data["notes"]
        
    if "lot_code" in data:
        doc["lot_code"] = data["lot_code"]
        
    if "external_lot_code" in data:
        doc["external_lot_code"] = data["external_lot_code"]
        
    if "is_mock_recall" in data:
        batch.is_mock_recall = data["is_mock_recall"]
        doc["is_mock_recall"] = data["is_mock_recall"]

    doc["updated_at"] = datetime.utcnow().isoformat() + "Z"
    batch.jsonb_doc = doc
    
    db.commit()
    db.refresh(batch)
    
    return batch
