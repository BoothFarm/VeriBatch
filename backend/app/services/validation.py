"""
Validation utilities for business rules
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models import database as db_models


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_batch_quantity(quantity: Optional[Dict[str, Any]]) -> None:
    """Validate that quantity has valid amount and unit"""
    if not quantity:
        return
    
    if "amount" not in quantity:
        raise ValidationError("Quantity must have 'amount' field")
    
    if "unit" not in quantity:
        raise ValidationError("Quantity must have 'unit' field")
    
    amount = quantity["amount"]
    if not isinstance(amount, (int, float)):
        raise ValidationError("Quantity amount must be a number")
    
    if amount < 0:
        raise ValidationError("Quantity amount cannot be negative")


def validate_split_quantities(
    db: Session,
    actor_id: str,
    source_batch_id: str,
    output_batches: List[Dict[str, Any]]
) -> None:
    """Validate that split outputs don't exceed source batch quantity"""
    # Get source batch
    source_batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.id == source_batch_id
    ).first()
    
    if not source_batch:
        raise ValidationError(f"Source batch {source_batch_id} not found")
    
    source_qty = source_batch.jsonb_doc.get("quantity")
    if not source_qty:
        # If no quantity tracked, allow split
        return
    
    source_amount = source_qty.get("amount", 0)
    source_unit = source_qty.get("unit", "unit")
    
    # Calculate total output
    total_output = 0
    for output in output_batches:
        output_qty = output.get("amount", {})
        output_amount = output_qty.get("amount", 0)
        output_unit = output_qty.get("unit", source_unit)
        
        # Simple validation: only check if units match
        if output_unit != source_unit:
            raise ValidationError(
                f"Output unit '{output_unit}' doesn't match source unit '{source_unit}'"
            )
        
        total_output += output_amount
    
    # Allow some tolerance for rounding/waste
    tolerance = source_amount * 0.01  # 1% tolerance
    if total_output > source_amount + tolerance:
        raise ValidationError(
            f"Split outputs ({total_output} {source_unit}) exceed source batch "
            f"quantity ({source_amount} {source_unit})"
        )


def validate_merge_quantities(
    db: Session,
    actor_id: str,
    source_batch_ids: List[str],
    output_quantity: Dict[str, Any]
) -> None:
    """Validate that merge output doesn't exceed total inputs"""
    total_input = 0
    common_unit = None
    
    for batch_id in source_batch_ids:
        batch = db.query(db_models.Batch).filter(
            db_models.Batch.actor_id == actor_id,
            db_models.Batch.id == batch_id
        ).first()
        
        if not batch:
            raise ValidationError(f"Source batch {batch_id} not found")
        
        qty = batch.jsonb_doc.get("quantity")
        if qty:
            amount = qty.get("amount", 0)
            unit = qty.get("unit", "unit")
            
            if common_unit is None:
                common_unit = unit
            elif unit != common_unit:
                raise ValidationError(
                    f"Cannot merge batches with different units: {common_unit} vs {unit}"
                )
            
            total_input += amount
    
    # Validate output
    output_amount = output_quantity.get("amount", 0)
    output_unit = output_quantity.get("unit", common_unit)
    
    if output_unit != common_unit:
        raise ValidationError(
            f"Output unit '{output_unit}' doesn't match input unit '{common_unit}'"
        )
    
    # Allow some tolerance for processing loss/waste
    tolerance = total_input * 0.05  # 5% tolerance for waste
    if output_amount > total_input + tolerance:
        raise ValidationError(
            f"Merge output ({output_amount} {output_unit}) exceeds total inputs "
            f"({total_input} {common_unit})"
        )


def validate_production_inputs(
    db: Session,
    actor_id: str,
    inputs: List[Dict[str, Any]]
) -> None:
    """Validate that input batches have sufficient quantity"""
    for input_ref in inputs:
        batch_id = input_ref.get("batch_id")
        requested_amount = input_ref.get("amount", {})
        
        if not batch_id:
            continue
        
        batch = db.query(db_models.Batch).filter(
            db_models.Batch.actor_id == input_ref.get("actor_id", actor_id),
            db_models.Batch.id == batch_id
        ).first()
        
        if not batch:
            raise ValidationError(f"Input batch {batch_id} not found")
        
        # Check if batch is in valid status
        if batch.status not in ["active", "quarantined"]:
            raise ValidationError(
                f"Input batch {batch_id} is not available (status: {batch.status})"
            )
        
        # Check quantity if specified
        if requested_amount:
            batch_qty = batch.jsonb_doc.get("quantity")
            if batch_qty:
                batch_amount = batch_qty.get("amount", 0)
                batch_unit = batch_qty.get("unit", "unit")
                req_amount = requested_amount.get("amount", 0)
                req_unit = requested_amount.get("unit", batch_unit)
                
                if req_unit != batch_unit:
                    raise ValidationError(
                        f"Requested unit '{req_unit}' doesn't match batch unit '{batch_unit}' "
                        f"for batch {batch_id}"
                    )
                
                if req_amount > batch_amount:
                    raise ValidationError(
                        f"Requested amount ({req_amount} {req_unit}) exceeds available "
                        f"quantity ({batch_amount} {batch_unit}) for batch {batch_id}"
                    )


def validate_date_order(production_date: Optional[str], expiration_date: Optional[str]) -> None:
    """Validate that expiration is after production"""
    if not production_date or not expiration_date:
        return
    
    # Simple string comparison works for ISO dates
    if expiration_date <= production_date:
        raise ValidationError(
            f"Expiration date ({expiration_date}) must be after production date ({production_date})"
        )
