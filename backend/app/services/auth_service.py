"""
Auth Service for user management
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models import database as db_models
from app.core import security

def get_user_by_email(db: Session, email: str) -> Optional[db_models.User]:
    return db.query(db_models.User).filter(db_models.User.email == email).first()

def create_user(db: Session, email: str, password: str, full_name: Optional[str] = None) -> db_models.User:
    hashed_password = security.get_password_hash(password)
    db_user = db_models.User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[db_models.User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user
