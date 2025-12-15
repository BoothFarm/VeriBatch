from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from app.db.database import get_db
from app.models import database as db_models
from app.core import security
from app.services import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False) # Point to your /token endpoint, or wherever your API token is issued.

async def get_current_user_from_token(
    request: Request,
    token: Annotated[Optional[str], Depends(oauth2_scheme)], 
    db: Session = Depends(get_db)
) -> db_models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from cookie if not in header
    if not token:
        cookie_auth = request.cookies.get("access_token")
        if cookie_auth:
            # cookie value is "Bearer <token>"
            scheme, _, param = cookie_auth.partition(" ")
            if scheme.lower() == "bearer":
                token = param
    
    if not token:
        raise credentials_exception
        
    try:
        payload = security.decode_access_token(token)
        if payload is None:
            raise credentials_exception
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = auth_service.get_user_by_email(db, email)
        if user is None:
            raise credentials_exception
        return user
    except Exception: # Handle JWTError specifically, or broader Exception if needed
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[db_models.User, Depends(get_current_user_from_token)]
) -> db_models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_user_and_owned_actor(
    actor_id: str,
    db: Session = Depends(get_db),
    current_user: Annotated[db_models.User, Depends(get_current_active_user)] = None
) -> db_models.Actor:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    actor = db.query(db_models.Actor).filter(
        db_models.Actor.id == actor_id, 
        db_models.Actor.owner_id == current_user.pk
    ).first()
    
    if not actor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found or not owned by user")
        
    return actor
