"""
OOJ Archive Export Service
Creates ZIP files containing all OOJ entities for an actor
"""
import io
import zipfile
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import database as db_models


def export_actor_ooj_archive(db: Session, actor_id: str) -> io.BytesIO:
    """
    Export all OOJ entities for an actor as a ZIP archive
    
    Structure:
    actor-{actor_id}/
        actor.json
        items/
            {item_id}.json
        batches/
            {batch_id}.json
        events/
            {event_id}.json
        processes/
            {process_id}.json
        locations/
            {location_id}.json
    """
    # Create in-memory ZIP
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        prefix = f"actor-{actor_id}"
        
        # Export actor
        actor = db.query(db_models.Actor).filter(
            db_models.Actor.id == actor_id
        ).first()
        
        if actor:
            zip_file.writestr(
                f"{prefix}/actor.json",
                json.dumps(actor.jsonb_doc, indent=2)
            )
        
        # Export items
        items = db.query(db_models.Item).filter(
            db_models.Item.actor_id == actor_id
        ).all()
        
        for item in items:
            zip_file.writestr(
                f"{prefix}/items/{item.id}.json",
                json.dumps(item.jsonb_doc, indent=2)
            )
        
        # Export batches
        batches = db.query(db_models.Batch).filter(
            db_models.Batch.actor_id == actor_id
        ).all()
        
        for batch in batches:
            zip_file.writestr(
                f"{prefix}/batches/{batch.id}.json",
                json.dumps(batch.jsonb_doc, indent=2)
            )
        
        # Export events
        events = db.query(db_models.Event).filter(
            db_models.Event.actor_id == actor_id
        ).all()
        
        for event in events:
            zip_file.writestr(
                f"{prefix}/events/{event.id}.json",
                json.dumps(event.jsonb_doc, indent=2)
            )
        
        # Export processes
        processes = db.query(db_models.Process).filter(
            db_models.Process.actor_id == actor_id
        ).all()
        
        for process in processes:
            zip_file.writestr(
                f"{prefix}/processes/{process.id}.json",
                json.dumps(process.jsonb_doc, indent=2)
            )
        
        # Export locations
        locations = db.query(db_models.Location).filter(
            db_models.Location.actor_id == actor_id
        ).all()
        
        for location in locations:
            zip_file.writestr(
                f"{prefix}/locations/{location.id}.json",
                json.dumps(location.jsonb_doc, indent=2)
            )
        
        # Add README
        readme = f"""# OOJ Archive for Actor: {actor_id}

This archive contains all Open Origin JSON (OOJ) v0.5 entities for this actor.

## Contents:
- actor.json - Actor profile
- items/ - Item definitions ({len(items)} items)
- batches/ - Batch records ({len(batches)} batches)
- events/ - Event history ({len(events)} events)
- processes/ - Process/recipe definitions ({len(processes)} processes)
- locations/ - Location records ({len(locations)} locations)

## Format:
All files are valid OOJ v0.5 JSON documents.

Each entity includes:
- schema: "open-origin-json/0.5"
- type: entity type
- id: unique identifier
- All OOJ-compliant fields

## Import:
These files can be imported into any OOJ-compliant system.

Generated: {db_models.func.now()}
"""
        zip_file.writestr(f"{prefix}/README.txt", readme)
    
    zip_buffer.seek(0)
    return zip_buffer


def get_export_summary(db: Session, actor_id: str) -> Dict[str, Any]:
    """Get summary of what would be exported"""
    actor = db.query(db_models.Actor).filter(
        db_models.Actor.id == actor_id
    ).first()
    
    if not actor:
        return None
    
    items_count = db.query(db_models.Item).filter(
        db_models.Item.actor_id == actor_id
    ).count()
    
    batches_count = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id
    ).count()
    
    events_count = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id
    ).count()
    
    processes_count = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor_id
    ).count()
    
    locations_count = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor_id
    ).count()
    
    return {
        "actor_id": actor_id,
        "actor_name": actor.name,
        "entities": {
            "items": items_count,
            "batches": batches_count,
            "events": events_count,
            "processes": processes_count,
            "locations": locations_count
        },
        "total_entities": items_count + batches_count + events_count + processes_count + locations_count + 1
    }
