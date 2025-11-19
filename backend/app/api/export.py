"""
Export API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.services import export_service

router = APIRouter(prefix="/actors/{actor_id}/export", tags=["export"])


@router.get("/summary")
def get_export_summary(actor_id: str, db: Session = Depends(get_db)):
    """
    Get summary of what would be exported for this actor
    
    Returns count of each entity type
    """
    summary = export_service.get_export_summary(db, actor_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Actor not found")
    
    return summary


@router.get("/ooj-archive")
def export_ooj_archive(actor_id: str, db: Session = Depends(get_db)):
    """
    Export all OOJ entities as a ZIP archive
    
    Returns a downloadable ZIP file containing:
    - actor.json
    - items/*.json
    - batches/*.json
    - events/*.json
    - processes/*.json
    - locations/*.json
    - README.txt
    """
    # Check if actor exists
    summary = export_service.get_export_summary(db, actor_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Actor not found")
    
    # Generate ZIP archive
    zip_buffer = export_service.export_actor_ooj_archive(db, actor_id)
    
    # Return as downloadable file
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"ooj-export-{actor_id}-{timestamp}.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
