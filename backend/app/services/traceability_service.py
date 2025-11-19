"""
Traceability service - Build upstream/downstream graphs from events
"""
from typing import Dict, List, Set, Any
from sqlalchemy.orm import Session
from app.models import database as db_models


def get_batch_traceability(
    db: Session,
    actor_id: str,
    batch_id: str,
    direction: str = "both"
) -> Dict[str, Any]:
    """
    Get traceability information for a batch
    
    Args:
        direction: "upstream", "downstream", or "both"
    
    Returns:
        {
            "batch_id": str,
            "upstream": [list of input batches],
            "downstream": [list of output batches],
            "events": [relevant events]
        }
    """
    result = {
        "batch_id": batch_id,
        "actor_id": actor_id,
        "upstream": [],
        "downstream": [],
        "events": []
    }
    
    # Get all events for this actor
    events = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id
    ).all()
    
    if direction in ["upstream", "both"]:
        # Find events where this batch is an output
        upstream_events = []
        for event in events:
            event_doc = event.jsonb_doc
            outputs = event_doc.get("outputs", [])
            
            for output in outputs:
                if output.get("batch_id") == batch_id:
                    upstream_events.append(event)
                    
                    # Get inputs from this event
                    inputs = event_doc.get("inputs", [])
                    for inp in inputs:
                        input_batch_id = inp.get("batch_id")
                        if input_batch_id and input_batch_id not in [b["batch_id"] for b in result["upstream"]]:
                            # Get batch details
                            batch = db.query(db_models.Batch).filter(
                                db_models.Batch.actor_id == inp.get("actor_id", actor_id),
                                db_models.Batch.id == input_batch_id
                            ).first()
                            
                            if batch:
                                result["upstream"].append({
                                    "batch_id": batch.id,
                                    "item_id": batch.item_id,
                                    "amount": inp.get("amount"),
                                    "status": batch.status,
                                    "event_id": event.id
                                })
        
        result["events"].extend([e.jsonb_doc for e in upstream_events])
    
    if direction in ["downstream", "both"]:
        # Find events where this batch is an input
        downstream_events = []
        for event in events:
            event_doc = event.jsonb_doc
            inputs = event_doc.get("inputs", [])
            
            for inp in inputs:
                if inp.get("batch_id") == batch_id:
                    downstream_events.append(event)
                    
                    # Get outputs from this event
                    outputs = event_doc.get("outputs", [])
                    for output in outputs:
                        output_batch_id = output.get("batch_id")
                        if output_batch_id and output_batch_id not in [b["batch_id"] for b in result["downstream"]]:
                            # Get batch details
                            batch = db.query(db_models.Batch).filter(
                                db_models.Batch.actor_id == output.get("actor_id", actor_id),
                                db_models.Batch.id == output_batch_id
                            ).first()
                            
                            if batch:
                                result["downstream"].append({
                                    "batch_id": batch.id,
                                    "item_id": batch.item_id,
                                    "amount": output.get("amount"),
                                    "status": batch.status,
                                    "event_id": event.id
                                })
        
        # Add downstream events (avoid duplicates)
        existing_event_ids = {e["id"] for e in result["events"]}
        for event in downstream_events:
            if event.id not in existing_event_ids:
                result["events"].append(event.jsonb_doc)
    
    # Remove duplicate events
    seen_ids = set()
    unique_events = []
    for event in result["events"]:
        if event["id"] not in seen_ids:
            seen_ids.add(event["id"])
            unique_events.append(event)
    
    result["events"] = unique_events
    
    return result


def get_full_traceability_graph(
    db: Session,
    actor_id: str,
    batch_id: str,
    max_depth: int = 10
) -> Dict[str, Any]:
    """
    Build a complete traceability graph recursively
    
    Returns a tree structure showing all upstream dependencies
    """
    visited: Set[str] = set()
    
    def build_tree(current_batch_id: str, depth: int = 0) -> Dict[str, Any]:
        if depth > max_depth or current_batch_id in visited:
            return {"batch_id": current_batch_id, "visited": True}
        
        visited.add(current_batch_id)
        
        # Get batch info
        batch = db.query(db_models.Batch).filter(
            db_models.Batch.actor_id == actor_id,
            db_models.Batch.id == current_batch_id
        ).first()
        
        if not batch:
            return {"batch_id": current_batch_id, "error": "not found"}
        
        node = {
            "batch_id": current_batch_id,
            "item_id": batch.item_id,
            "status": batch.status,
            "production_date": batch.production_date,
            "quantity": batch.jsonb_doc.get("quantity"),
            "inputs": [],
            "depth": depth
        }
        
        # Find events where this batch is an output
        events = db.query(db_models.Event).filter(
            db_models.Event.actor_id == actor_id
        ).all()
        
        for event in events:
            event_doc = event.jsonb_doc
            outputs = event_doc.get("outputs", [])
            
            # Check if this batch is an output of this event
            is_output = any(o.get("batch_id") == current_batch_id for o in outputs)
            
            if is_output:
                # Get inputs and recurse
                inputs = event_doc.get("inputs", [])
                for inp in inputs:
                    input_batch_id = inp.get("batch_id")
                    if input_batch_id:
                        input_tree = build_tree(input_batch_id, depth + 1)
                        node["inputs"].append({
                            "batch": input_tree,
                            "amount": inp.get("amount"),
                            "event_id": event.id,
                            "event_type": event_doc.get("event_type")
                        })
        
        return node
    
    return build_tree(batch_id)


def get_item_traceability_summary(
    db: Session,
    actor_id: str,
    item_id: str
) -> Dict[str, Any]:
    """
    Get a summary of all batches and their relationships for an item
    """
    batches = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.item_id == item_id
    ).all()
    
    batch_summaries = []
    
    for batch in batches:
        trace = get_batch_traceability(db, actor_id, batch.id, direction="upstream")
        
        batch_summaries.append({
            "batch_id": batch.id,
            "status": batch.status,
            "production_date": batch.production_date,
            "quantity": batch.jsonb_doc.get("quantity"),
            "input_count": len(trace["upstream"]),
            "event_count": len(trace["events"])
        })
    
    return {
        "item_id": item_id,
        "total_batches": len(batches),
        "batches": batch_summaries
    }
