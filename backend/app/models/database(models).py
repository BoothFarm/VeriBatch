"""
SQLAlchemy database models with JSONB storage for OOJ entities
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class Actor(Base):
    __tablename__ = "actors"
    
    pk = Column(Integer, primary_key=True, index=True)
    id = Column(String, unique=True, index=True, nullable=False)
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
