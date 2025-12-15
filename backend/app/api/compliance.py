from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import database as db_models
from app.api.frontend import get_current_user_from_cookie
from app.services import compliance_service
from typing import Optional

router = APIRouter(tags=["compliance"])

@router.get("/actors/{actor_id}/compliance/recall-report/{batch_id}")
def get_recall_report(
    actor_id: str,
    batch_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """
    Generate a CanadaGAP/SFCR compliant recall report for a specific batch.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify ownership
    actor = db.query(db_models.Actor).filter(db_models.Actor.id == actor_id, db_models.Actor.owner_id == user.pk).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    try:
        report = compliance_service.generate_recall_report(db, actor_id, batch_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
