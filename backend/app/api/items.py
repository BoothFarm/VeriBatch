"""
API routes for items
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated # Add Annotated
from datetime import datetime

from app.db.database import get_db
from app.models import database as db_models
from ooj_client import entities
from app.dependencies import get_current_active_user_and_owned_actor # Add this import

router = APIRouter(prefix="/actors/{actor_id}/items", tags=["items"])


@router.post("", response_model=dict)
def create_item(
    item_data: dict, # Body parameter without default
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)], # Dependency with default
    db: Annotated[Session, Depends(get_db)] # Dependency with default
):
    """Create a new item (Protected)"""
    try:
        now = datetime.utcnow().isoformat() + "Z"
        
        # Ensure required OOJ fields
        if "schema" not in item_data:
            item_data["schema"] = entities.SCHEMA_VERSION
        if "type" not in item_data:
            item_data["type"] = "item"
        item_data["actor_id"] = actor.id # Use actor.id from dependency
        if "created_at" not in item_data:
            item_data["created_at"] = now
        item_data["updated_at"] = now
        
        # Check if item already exists
        existing = db.query(db_models.Item).filter(
            db_models.Item.actor_id == actor.id, # Use actor.id from dependency
            db_models.Item.id == item_data["id"]
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item already exists for this actor")
        
        db_item = db_models.Item(
            id=item_data["id"],
            actor_id=actor.id, # Use actor.id from dependency
            name=item_data["name"],
            category=item_data.get("category"),
            jsonb_doc=item_data
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        return db_item.jsonb_doc
    
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {e}")


@router.get("", response_model=List[dict])
def list_items(
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)], # Dependency with default
    db: Annotated[Session, Depends(get_db)], # Dependency with default
    category: Optional[str] = None, # Query parameter with default
):
    """List all items for an actor (Protected)"""
    query = db.query(db_models.Item).filter(db_models.Item.actor_id == actor.id) # Use actor.id from dependency
    
    if category:
        query = query.filter(db_models.Item.category == category)
    
    items = query.all()
    return [item.jsonb_doc for item in items]


@router.get("/{item_id}", response_model=dict)
def get_item(
    item_id: str, # Path parameter without default
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)], # Dependency with default
    db: Annotated[Session, Depends(get_db)] # Dependency with default
):
    """Get a specific item (Protected)"""
    item = db.query(db_models.Item).filter(
        db_models.Item.actor_id == actor.id, # Use actor.id from dependency
        db_models.Item.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    return item.jsonb_doc


@router.patch("/{item_id}", response_model=dict)
def update_item(
    item_id: str, # Path parameter
    item_data: dict, # Body parameter
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)], # Dependency
    db: Annotated[Session, Depends(get_db)] # Dependency
):
    """Update an existing item (Protected)"""
    item = db.query(db_models.Item).filter(
        db_models.Item.actor_id == actor.id,
        db_models.Item.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    # Update fields
    if "name" in item_data:
        item.name = item_data["name"]
        
    if "category" in item_data:
        item.category = item_data["category"]
        
    # Update JSON doc
    doc = item.jsonb_doc.copy()
    for key, value in item_data.items():
        if value is None:
            doc.pop(key, None)
        else:
            doc[key] = value
    doc["updated_at"] = datetime.utcnow().isoformat() + "Z"
    item.jsonb_doc = doc
    
    db.commit()
    db.refresh(item)
    
    return item.jsonb_doc


@router.delete("/{item_id}", response_model=dict)
def delete_item(
    item_id: str, # Path parameter
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)], # Dependency
    db: Annotated[Session, Depends(get_db)] # Dependency
):
    """Delete an item (Protected)"""
    item = db.query(db_models.Item).filter(
        db_models.Item.actor_id == actor.id,
        db_models.Item.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    db.delete(item)
    db.commit()
    
    return {"message": "Item deleted successfully"}
