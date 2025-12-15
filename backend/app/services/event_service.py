"""
Service layer for event operations (Level 2)
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models import database as db_models
from ooj_client import entities
from app.services import batch_service
from app.services.validation import (
    validate_split_quantities,
    validate_merge_quantities,
    validate_production_inputs,
    ValidationError
)


def record_processing_event(
    db: Session,
    event_id: str,
    actor_id: str,
    process_id: Optional[str],
    inputs: List[Dict[str, Any]],
    outputs: List[Dict[str, Any]],
    location_id: Optional[str] = None,
    packaging_materials: Optional[List[Dict[str, Any]]] = None,
    waste: Optional[Dict[str, Any]] = None,
    performed_by: Optional[str] = None,
    notes: Optional[str] = None,
    timestamp: Optional[str] = None
) -> db_models.Event:
    """
    Record a processing event and automatically:
    1. Create output batches
    2. Update input batch statuses if fully consumed
    3. Track packaging materials used
    """
    # Validate inputs have sufficient quantity
    validate_production_inputs(db, actor_id, inputs)
    
    now = datetime.utcnow().isoformat() + "Z"
    if not timestamp:
        timestamp = now
    
    # Build event entity
    event_data = {
        "schema": entities.SCHEMA_VERSION,
        "type": "event",
        "id": event_id,
        "actor_id": actor_id,
        "timestamp": timestamp,
        "event_type": "processing",
        "created_at": now,
        "updated_at": now
    }
    
    if process_id:
        event_data["process_id"] = process_id
    if location_id:
        event_data["location_id"] = location_id
    if performed_by:
        event_data["performed_by"] = performed_by
    if notes:
        event_data["notes"] = notes
    
    # Add waste
    if waste:
        event_data["waste"] = waste
    
    # Add inputs
    if inputs:
        event_data["inputs"] = inputs
        # Deduct used quantities from input batches
        for input_data in inputs:
            batch_id = input_data.get("batch_id")
            used_qty = input_data.get("amount") # {amount: X, unit: Y}
            
            if batch_id and used_qty:
                batch = batch_service.get_batch(db, actor_id, batch_id)
                if batch:
                    current_qty = batch.jsonb_doc.get("quantity")
                    if current_qty:
                        current_unit = current_qty.get("unit")
                        used_unit = used_qty.get("unit", current_unit) # Default to batch unit
                        
                        if current_unit == used_unit:
                            new_amount = max(0, current_qty.get("amount", 0) - used_qty.get("amount", 0))
                            
                            # Update Quantity
                            batch_service.update_batch_details(db, actor_id, batch_id, {
                                "quantity": {
                                    "amount": new_amount,
                                    "unit": current_unit
                                }
                            })
                            
                            # Update Status if depleted
                            if new_amount <= 0:
                                batch_service.update_batch_status(db, actor_id, batch_id, "depleted")
        
    # Add outputs
    if outputs:
        event_data["outputs"] = outputs
        # Create output batches automatically
        for output in outputs:
            batch_id = output.get("batch_id")
            if batch_id:
                # Check if batch already exists
                existing_batch = batch_service.get_batch(db, actor_id, batch_id)
                if not existing_batch:
                    # Create new batch from output specification
                    quantity = output.get("amount")
                    if quantity:
                        quantity_obj = entities.Quantity(
                            amount=quantity["amount"],
                            unit=quantity["unit"]
                        )
                    else:
                        quantity_obj = None
                    
                    batch_service.create_batch(
                        db=db,
                        batch_id=batch_id,
                        actor_id=actor_id,
                        item_id=output.get("item_id", "unknown"),
                        quantity=quantity_obj,
                        status="active",
                        production_date=timestamp.split("T")[0] if "T" in timestamp else timestamp,
                        origin_kind="transformed",
                        location_id=location_id
                    )
    
    # Add packaging materials
    if packaging_materials:
        event_data["packaging_materials"] = packaging_materials
    
    # Create event
    db_event = db_models.Event(
        id=event_id,
        actor_id=actor_id,
        event_type="processing",
        timestamp=timestamp,
        jsonb_doc=event_data
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event


def split_batch(
    db: Session,
    event_id: str,
    actor_id: str,
    source_batch_id: str,
    output_batches: List[Dict[str, Any]],
    location_id: Optional[str] = None,
    notes: Optional[str] = None,
    timestamp: Optional[str] = None
) -> db_models.Event:
    """
    Split a batch into multiple new batches
    Creates a split event and new batch records
    """
    # Validate split quantities
    validate_split_quantities(db, actor_id, source_batch_id, output_batches)
    
    now = datetime.utcnow().isoformat() + "Z"
    if not timestamp:
        timestamp = now
    
    # Get source batch
    source_batch = batch_service.get_batch(db, actor_id, source_batch_id)
    if not source_batch:
        raise ValueError(f"Source batch {source_batch_id} not found")
    
    source_doc = source_batch.jsonb_doc
    
    # Calculate total output quantity
    total_amount = sum(
        output.get("amount", {}).get("amount", 0) 
        for output in output_batches
    )
    
    # Build split event
    event_data = {
        "schema": entities.SCHEMA_VERSION,
        "type": "event",
        "id": event_id,
        "actor_id": actor_id,
        "timestamp": timestamp,
        "event_type": "split",
        "inputs": [{
            "batch_id": source_batch_id,
            "amount": source_doc.get("quantity")
        }],
        "outputs": output_batches,
        "created_at": now,
        "updated_at": now
    }
    
    if location_id:
        event_data["location_id"] = location_id
    if notes:
        event_data["notes"] = notes
    
    # Create output batches
    for output in output_batches:
        batch_id = output.get("batch_id")
        amount = output.get("amount", {})
        
        if batch_id:
            quantity_obj = entities.Quantity(
                amount=amount.get("amount", 0),
                unit=amount.get("unit", source_doc.get("quantity", {}).get("unit", "unit"))
            )
            
            batch_service.create_batch(
                db=db,
                batch_id=batch_id,
                actor_id=actor_id,
                item_id=source_batch.item_id,
                quantity=quantity_obj,
                status="active",
                production_date=source_batch.production_date,
                origin_kind="split",
                location_id=location_id or source_batch.jsonb_doc.get("location_id")
            )
    
    # Update source batch to depleted
    batch_service.update_batch_status(db, actor_id, source_batch_id, "depleted")
    
    # Create event
    db_event = db_models.Event(
        id=event_id,
        actor_id=actor_id,
        event_type="split",
        timestamp=timestamp,
        jsonb_doc=event_data
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event


def merge_batches(
    db: Session,
    event_id: str,
    actor_id: str,
    source_batch_ids: List[str],
    output_batch_id: str,
    output_quantity: Dict[str, Any],
    location_id: Optional[str] = None,
    notes: Optional[str] = None,
    timestamp: Optional[str] = None
) -> db_models.Event:
    """
    Merge multiple batches into one
    Creates a merge event and new output batch
    """
    # Validate merge quantities
    validate_merge_quantities(db, actor_id, source_batch_ids, output_quantity)
    
    now = datetime.utcnow().isoformat() + "Z"
    if not timestamp:
        timestamp = now
    
    # Get all source batches
    source_batches = []
    item_id = None
    
    for batch_id in source_batch_ids:
        batch = batch_service.get_batch(db, actor_id, batch_id)
        if not batch:
            raise ValueError(f"Source batch {batch_id} not found")
        source_batches.append(batch)
        
        if not item_id:
            item_id = batch.item_id
        elif item_id != batch.item_id:
            raise ValueError("Cannot merge batches of different items")
    
    # Build merge event
    inputs = [
        {
            "batch_id": batch.id,
            "amount": batch.jsonb_doc.get("quantity")
        }
        for batch in source_batches
    ]
    
    event_data = {
        "schema": entities.SCHEMA_VERSION,
        "type": "event",
        "id": event_id,
        "actor_id": actor_id,
        "timestamp": timestamp,
        "event_type": "merge",
        "inputs": inputs,
        "outputs": [{
            "batch_id": output_batch_id,
            "amount": output_quantity
        }],
        "created_at": now,
        "updated_at": now
    }
    
    if location_id:
        event_data["location_id"] = location_id
    if notes:
        event_data["notes"] = notes
    
    # Create output batch
    quantity_obj = entities.Quantity(
        amount=output_quantity.get("amount", 0),
        unit=output_quantity.get("unit", "unit")
    )
    
    batch_service.create_batch(
        db=db,
        batch_id=output_batch_id,
        actor_id=actor_id,
        item_id=item_id,
        quantity=quantity_obj,
        status="active",
        production_date=timestamp.split("T")[0] if "T" in timestamp else timestamp,
        origin_kind="merged",
        location_id=location_id
    )
    
    # Mark source batches as depleted
    for batch_id in source_batch_ids:
        batch_service.update_batch_status(db, actor_id, batch_id, "depleted")
    
    # Create event
    db_event = db_models.Event(
        id=event_id,
        actor_id=actor_id,
        event_type="merge",
        timestamp=timestamp,
        jsonb_doc=event_data
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event


    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event


def get_event(db: Session, actor_id: str, event_id: str) -> Optional[db_models.Event]:
    """Get a specific event"""
    return db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id,
        db_models.Event.id == event_id
    ).first()


def update_event(
    db: Session,
    actor_id: str,
    event_id: str,
    data: dict
) -> Optional[db_models.Event]:
    """Update event metadata (notes, timestamp, etc.)"""
    event = get_event(db, actor_id, event_id)
    if not event:
        return None
        
    # Update fields
    if "timestamp" in data:
        event.timestamp = data["timestamp"]
        
    # Update JSON doc
    doc = event.jsonb_doc.copy()
    
    for key, value in data.items():
        if value is None:
            doc.pop(key, None)
        else:
            doc[key] = value
        
    doc["updated_at"] = datetime.utcnow().isoformat() + "Z"
    event.jsonb_doc = doc
    
    db.commit()
    db.refresh(event)
    
    return event
