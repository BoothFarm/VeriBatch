"""
Export API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import datetime

from app.db.database import get_db
from app.services import export_service, traceability_service
from app.models import database as db_models
from app.dependencies import get_current_active_user_and_owned_actor

router = APIRouter(prefix="/actors/{actor_id}/export", tags=["export"])


@router.get("/summary")
def get_export_summary(
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get summary of what would be exported for this actor (Protected)
    
    Returns count of each entity type
    """
    summary = export_service.get_export_summary(db, actor.id)
    
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found")
    
    return summary


@router.get("/ooj-archive")
def export_ooj_archive(
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Export all OOJ entities as a ZIP archive (Protected)
    """
    summary = export_service.get_export_summary(db, actor.id)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found")
    
    zip_buffer = export_service.export_actor_ooj_archive(db, actor.id)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"ooj-export-{actor.id}-{timestamp}.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/items/{item_id}")
def export_item(
    item_id: str,
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Export single item as JSON"""
    item = db.query(db_models.Item).filter(
        db_models.Item.actor_id == actor.id,
        db_models.Item.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    return JSONResponse(
        content=item.jsonb_doc,
        headers={"Content-Disposition": f"attachment; filename=item-{item_id}.json"}
    )


@router.get("/batches/{batch_id}")
def export_batch(
    batch_id: str,
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Export single batch as JSON"""
    batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor.id,
        db_models.Batch.id == batch_id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    return JSONResponse(
        content=batch.jsonb_doc,
        headers={"Content-Disposition": f"attachment; filename=batch-{batch_id}.json"}
    )


@router.get("/events/{event_id}")
def export_event(
    event_id: str,
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Export single event as JSON"""
    event = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor.id,
        db_models.Event.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return JSONResponse(
        content=event.jsonb_doc,
        headers={"Content-Disposition": f"attachment; filename=event-{event_id}.json"}
    )


@router.get("/locations/{location_id}")
def export_location(
    location_id: str,
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Export single location as JSON"""
    location = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor.id,
        db_models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
        
    return JSONResponse(
        content=location.jsonb_doc,
        headers={"Content-Disposition": f"attachment; filename=location-{location_id}.json"}
    )


@router.get("/processes/{process_id}")
def export_process(
    process_id: str,
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Export single process as JSON"""
    process = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor.id,
        db_models.Process.id == process_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
        
    return JSONResponse(
        content=process.jsonb_doc,
        headers={"Content-Disposition": f"attachment; filename=process-{process_id}.json"}
    )


@router.get("/traceability/{batch_id}")
def export_traceability_graph(
    batch_id: str,
    actor: Annotated[db_models.Actor, Depends(get_current_active_user_and_owned_actor)],
    db: Annotated[Session, Depends(get_db)]
):
    """Export full traceability graph for a batch"""
    # Check if batch exists first
    batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor.id,
        db_models.Batch.id == batch_id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    graph = traceability_service.get_full_traceability_graph(db, actor.id, batch_id)
    
    return JSONResponse(
        content=graph,
        headers={"Content-Disposition": f"attachment; filename=traceability-{batch_id}.json"}
    )
