"""
Advanced batch operations API (Level 2)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Annotated
from datetime import datetime

from app.db.database import get_db
from app.services import event_service
from app.services.validation import ValidationError
from app.models import database as db_models
from app.dependencies import get_current_active_user_and_owned_actor # Add this import

router = APIRouter(prefix="/actors/{actor_id}/operations", tags=["operations"])


@router.post("/split-batch", response_model=dict)
def split_batch_operation(
    operation: Dict[str, Any],
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Split a batch into multiple batches (Protected)
    
    Body:
    {
        "event_id": "evt-split-001",
        "source_batch_id": "batch-001",
        "outputs": [
            {"batch_id": "batch-001a", "amount": {"amount": 10, "unit": "kg"}},
            {"batch_id": "batch-001b", "amount": {"amount": 15, "unit": "kg"}}
        ],
        "location_id": "kitchen-main",
        "notes": "Split for different markets"
    }
    """
    try:
        event = event_service.split_batch(
            db=db,
            event_id=operation["event_id"],
            actor_id=actor.id, # Use actor.id from dependency
            source_batch_id=operation["source_batch_id"],
            output_batches=operation["outputs"],
            location_id=operation.get("location_id"),
            notes=operation.get("notes"),
            timestamp=operation.get("timestamp")
        )
        return event.jsonb_doc
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {e}")


@router.post("/merge-batches", response_model=dict)
def merge_batches_operation(
    operation: Dict[str, Any],
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Merge multiple batches into one (Protected)
    
    Body:
    {
        "event_id": "evt-merge-001",
        "source_batch_ids": ["batch-001", "batch-002"],
        "output_batch_id": "batch-merged-001",
        "output_quantity": {"amount": 25, "unit": "kg"},
        "location_id": "warehouse",
        "notes": "Consolidated batches"
    }
    """
    try:
        event = event_service.merge_batches(
            db=db,
            event_id=operation["event_id"],
            actor_id=actor.id, # Use actor.id from dependency
            source_batch_ids=operation["source_batch_ids"],
            output_batch_id=operation["output_batch_id"],
            output_quantity=operation["output_quantity"],
            location_id=operation.get("location_id"),
            notes=operation.get("notes"),
            timestamp=operation.get("timestamp")
        )
        return event.jsonb_doc
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {e}")


@router.post("/dispose-batch", response_model=dict)
def dispose_batch_operation(
    operation: Dict[str, Any],
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Dispose of a batch (Protected)
    
    Body:
    {
        "event_id": "evt-dispose-001",
        "batch_id": "batch-001",
        "reason": "expired",
        "location_id": "compost-area",
        "notes": "Past best-before date"
    }
    """
    try:
        event = event_service.dispose_batch(
            db=db,
            event_id=operation["event_id"],
            actor_id=actor.id, # Use actor.id from dependency
            batch_id=operation["batch_id"],
            reason=operation["reason"],
            location_id=operation.get("location_id"),
            notes=operation.get("notes"),
            timestamp=operation.get("timestamp")
        )
        return event.jsonb_doc
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {e}")


@router.post("/production-run", response_model=dict)
def production_run_operation(
    operation: Dict[str, Any],
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Record a complete production run (Protected)
    
    Body:
    {
        "event_id": "evt-prod-001",
        "process_id": "proc-pickled-garlic-v1",
        "inputs": [
            {"batch_id": "garlic-raw-001", "amount": {"amount": 8, "unit": "kg"}}
        ],
        "outputs": [
            {"batch_id": "pg-2025-01", "item_id": "pickled-garlic", "amount": {"amount": 42, "unit": "jar_500ml"}}
        ],
        "packaging_materials": [
            {"batch_id": "jars-batch-001", "amount": {"amount": 42, "unit": "unit"}}
        ],
        "location_id": "kitchen-main",
        "performed_by": "Jane Smith",
        "notes": "Batch processed successfully"
    }
    """
    try:
        event = event_service.record_processing_event(
            db=db,
            event_id=operation["event_id"],
            actor_id=actor.id, # Use actor.id from dependency
            process_id=operation.get("process_id"),
            inputs=operation["inputs"],
            outputs=operation["outputs"],
            location_id=operation.get("location_id"),
            packaging_materials=operation.get("packaging_materials"),
            performed_by=operation.get("performed_by"),
            notes=operation.get("notes"),
            timestamp=operation.get("timestamp")
        )
        return event.jsonb_doc
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {e}")
