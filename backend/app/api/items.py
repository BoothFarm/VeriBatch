"""
API routes for items
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities

router = APIRouter(prefix="/actors/{actor_id}/items", tags=["items"])


@router.post("", response_model=dict)
def create_item(actor_id: str, item_data: dict, db: Session = Depends(get_db)):
    """Create a new item"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in item_data:
            item_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in item_data:
            item_data["type"] = "item"
        item_data["actor_id"] = actor_id
        if "created_at" not in item_data:
            item_data["created_at"] = now
        item_data["updated_at"] = now
        
        # Check if item already exists
        existing = db.query(db_models.Item).filter(
            db_models.Item.actor_id == actor_id,
            db_models.Item.id == item_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Item already exists")
        
        db_item = db_models.Item(
            id=item_data["id"],
            actor_id=actor_id,
            name=item_data["name"],
            category=item_data.get("category"),
            jsonb_doc=item_data
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        return db_item.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")


@router.get("", response_model=List[dict])
def list_items(actor_id: str, category: Optional[str] = None, db: Session = Depends(get_db)):
    """List all items for an actor"""
    query = db.query(db_models.Item).filter(db_models.Item.actor_id == actor_id)
    
    if category:
        query = query.filter(db_models.Item.category == category)
    
    items = query.all()
    return [item.jsonb_doc for item in items]


@router.get("/{item_id}", response_model=dict)
def get_item(actor_id: str, item_id: str, db: Session = Depends(get_db)):
    """Get a specific item"""
    item = db.query(db_models.Item).filter(
        db_models.Item.actor_id == actor_id,
        db_models.Item.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item.jsonb_doc
