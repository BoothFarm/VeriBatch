"""
Traceability API endpoints (Level 2/3)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.services import traceability_service

router = APIRouter(prefix="/actors/{actor_id}/traceability", tags=["traceability"])


@router.get("/batches/{batch_id}")
def get_batch_trace(
    actor_id: str,
    batch_id: str,
    direction: str = Query("both", regex="^(upstream|downstream|both)$"),
    db: Session = Depends(get_db)
):
    """
    Get traceability information for a specific batch
    
    Query params:
    - direction: "upstream" (inputs), "downstream" (outputs), or "both"
    
    Returns:
    - upstream: List of batches that went into this batch
    - downstream: List of batches that came from this batch
    - events: Related events
    """
    result = traceability_service.get_batch_traceability(
        db=db,
        actor_id=actor_id,
        batch_id=batch_id,
        direction=direction
    )
    
    if not result["upstream"] and not result["downstream"] and not result["events"]:
        # Check if batch exists
        from app.services import batch_service
        batch = batch_service.get_batch(db, actor_id, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
    
    return result


@router.get("/batches/{batch_id}/graph")
def get_batch_graph(
    actor_id: str,
    batch_id: str,
    max_depth: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get full traceability graph (tree) for a batch
    
    Query params:
    - max_depth: Maximum recursion depth (default 10, max 20)
    
    Returns a nested tree structure showing all input dependencies
    """
    from app.services import batch_service
    batch = batch_service.get_batch(db, actor_id, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    graph = traceability_service.get_full_traceability_graph(
        db=db,
        actor_id=actor_id,
        batch_id=batch_id,
        max_depth=max_depth
    )
    
    return graph


@router.get("/items/{item_id}/summary")
def get_item_trace_summary(
    actor_id: str,
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    Get traceability summary for all batches of an item
    
    Returns statistics and overview of all batches for this item
    """
    summary = traceability_service.get_item_traceability_summary(
        db=db,
        actor_id=actor_id,
        item_id=item_id
    )
    
    if summary["total_batches"] == 0:
        raise HTTPException(status_code=404, detail="No batches found for this item")
    
    return summary
