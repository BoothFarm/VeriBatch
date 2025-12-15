"""
SQLAlchemy database models with JSONB storage for OOJ entities
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Index, Float, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"
    
    pk = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship: One user can own multiple actors (sub-accounts)
    actors = relationship("Actor", back_populates="owner")


class Actor(Base):
    __tablename__ = "actors"
    
    pk = Column(Integer, primary_key=True, index=True)
    id = Column(String, unique=True, index=True, nullable=False)
    
    # Owner (User) relationship
    owner_id = Column(Integer, ForeignKey("users.pk"), nullable=True, index=True)
    owner = relationship("User", back_populates="actors")
    
    name = Column(String, nullable=False)
    kind = Column(String, index=True)
    jsonb_doc = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_actors_id', 'id'),
    )


class Item(Base):
    __tablename__ = "items"
    
    pk = Column(Integer, primary_key=True, index=True)
    id = Column(String, nullable=False)
    actor_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, index=True)
    jsonb_doc = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_items_actor_id', 'actor_id', 'id', unique=True),
    )


class Batch(Base):
    __tablename__ = "batches"
    
    pk = Column(Integer, primary_key=True, index=True)
    id = Column(String, nullable=False)
    actor_id = Column(String, nullable=False, index=True)
    item_id = Column(String, nullable=False, index=True)
    status = Column(String, index=True, default="active")
    production_date = Column(String)
    expiration_date = Column(String)
    is_mock_recall = Column(Boolean, default=False, index=True)
    jsonb_doc = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_batches_actor_id', 'actor_id', 'id', unique=True),
        Index('idx_batches_item', 'item_id'),
        Index('idx_batches_status', 'status'),
    )


class Process(Base):
    __tablename__ = "processes"
    
    pk = Column(Integer, primary_key=True, index=True)
    id = Column(String, nullable=False)
    actor_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, index=True)
    version = Column(String)
    jsonb_doc = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_processes_actor_id', 'actor_id', 'id', unique=True),
    )


class Event(Base):
    __tablename__ = "events"
    
    pk = Column(Integer, primary_key=True, index=True)
    id = Column(String, nullable=False)
    actor_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    timestamp = Column(String, nullable=False, index=True)
    jsonb_doc = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_events_actor_id', 'actor_id', 'id', unique=True),
        Index('idx_events_type', 'event_type'),
        Index('idx_events_timestamp', 'timestamp'),
    )


class Location(Base):
    __tablename__ = "locations"
    
    pk = Column(Integer, primary_key=True, index=True)
    id = Column(String, nullable=False)
    actor_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, index=True)
    jsonb_doc = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_locations_actor_id', 'actor_id', 'id', unique=True),
    )


class LabelTemplate(Base):
    __tablename__ = "label_templates"
    
    pk = Column(Integer, primary_key=True, index=True)
    id = Column(String, nullable=False)
    actor_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    width_in = Column(Float, nullable=False)
    height_in = Column(Float, nullable=False)
    jsonb_doc = Column(JSONB, nullable=False) # Stores the 'elements' array
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_label_templates_actor_id', 'actor_id', 'id', unique=True),
    )