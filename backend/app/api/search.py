from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models import database as db_models
from app.services import search_service, auth_service
from app.core import security
from fastapi import Cookie

router = APIRouter(tags=["search"])

# --- Auth Dependency (Duplicate from frontend.py for now, ideally shared) ---
def get_current_user_from_cookie(request: Request, access_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        return None
    
    try:
        scheme, token = access_token.split()
        if scheme.lower() != 'bearer':
            return None
        payload = security.decode_access_token(token)
        if not payload:
            return None
    except (ValueError, AttributeError):
        return None
        
    email = payload.get("sub")
    if not email:
        return None
    
    return auth_service.get_user_by_email(db, email)

@router.get("/search")
def search(
    request: Request,
    q: str = Query(..., min_length=1),
    actor_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Determine which actors to search
    target_actor_ids = []
    
    if actor_id:
        # Check ownership
        actor = next((a for a in user.actors if a.id == actor_id), None)
        if not actor:
            raise HTTPException(status_code=403, detail="Access denied to this actor")
        target_actor_ids.append(actor.id)
    else:
        # Search all user's actors
        target_actor_ids = [a.id for a in user.actors]
    
    if not target_actor_ids:
        return []

    # Perform search
    # We loop through actors or construct a complex filter. 
    # For now, let's just search the primary actor if multiple (or all if we update service).
    # Update: Search service currently takes a single ID. 
    # Let's simple-loop it for now since users rarely have > 3 farms.
    # OR better: update search_service to handle list.
    
    results = []
    for aid in target_actor_ids:
        # We limit results per actor to avoid noise
        results.extend(search_service.search_global(q, aid, limit=5))
    
    # Sort combined results by relevance/score is hard without Meilisearch doing it.
    # But Meilisearch returns sorted results. 
    # If we have multiple actors, we might interleave them?
    # Let's just return the results.
    
    return results
