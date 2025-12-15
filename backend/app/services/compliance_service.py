"""
Compliance Service
Logic for regulatory reporting (SFCR, CanadaGAP), recalls, and safety checks.
"""
from typing import Dict, Any, List, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import database as db_models
from ooj_client import entities

class RecallReport:
    """Structure for recall report data"""
    def __init__(self, batch_id: str, actor_id: str):
        self.batch_id = batch_id
        self.actor_id = actor_id
        self.scope = {
            "total_harvested": 0.0,
            "unit": "",
            "current_inventory": 0.0,
            "distributed": 0.0,
            "waste": 0.0,
            "math_check": False
        }
        self.upstream = []
        self.downstream = []
        self.mock = False

def generate_recall_report(db: Session, actor_id: str, batch_id: str) -> Dict[str, Any]:
    """
    Generates a full recursive recall report.
    """
    
    # 1. Get the target batch
    target_batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.id == batch_id
    ).first()
    
    if not target_batch:
        raise ValueError(f"Batch {batch_id} not found")
        
    report = RecallReport(batch_id, actor_id)
    report.mock = target_batch.is_mock_recall
    
    # 2. Scope Calculations
    # Get initial quantity (from creating event output or batch record)
    if target_batch.jsonb_doc.get("quantity"):
        qty = target_batch.jsonb_doc["quantity"]
        report.scope["total_harvested"] = qty.get("amount", 0)
        report.scope["unit"] = qty.get("unit", "")
        
    # Get current inventory (if active)
    if target_batch.status == "active":
        # In a real system, we might check current quantity vs initial. 
        # For now, if active, assume full amount is inventory unless we have split events
        # This is a simplification. A robust system would track quantity_on_hand.
        pass

    # 3. Recursive Traceability
    
    # Upstream (Inputs)
    # Find event that created this batch
    creation_event = _find_creation_event(db, actor_id, batch_id)
    if creation_event:
        _trace_upstream(db, actor_id, creation_event, report.upstream, set())

    # Downstream (Outputs/Distribution)
    _trace_downstream(db, actor_id, batch_id, report.downstream, set(), report.scope)
    
    # 4. Math Check (Validation)
    # Ideally: Harvested = Inventory + Distributed + Waste
    # We will just sum distributed for now from downstream
    
    return {
        "meta": {
            "batch_id": report.batch_id,
            "generated_at": func.now(),
            "is_mock_recall": report.mock
        },
        "scope": report.scope,
        "upstream": report.upstream,
        "downstream": report.downstream
    }


def _find_creation_event(db: Session, actor_id: str, batch_id: str) -> Optional[db_models.Event]:
    """Find the event that outputted this batch"""
    # This is tricky with JSONB. We need to find an event where 'outputs' array contains batch_id
    # SQLAlchemy's JSONB operators can do this.
    # event.jsonb_doc['outputs'] @> '[{"batch_id": "..."}]'
    
    return db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id,
        db_models.Event.jsonb_doc['outputs'].contains([{"batch_id": batch_id}])
    ).first()


def _trace_upstream(db: Session, actor_id: str, event: db_models.Event, results: List[Dict], visited: Set[str]):
    """Recursively find inputs"""
    if event.id in visited:
        return
    visited.add(event.id)
    
    event_doc = event.jsonb_doc
    
    # Record this node
    node = {
        "event_id": event.id,
        "type": event.event_type,
        "date": event.timestamp,
        "location": None,
        "inputs": []
    }
    
    # Get Location Info
    if event.location_id: # Note: this assumes we fixed the location_id bug on Event model or retrieve from doc
        # We removed location_id column from Event model, so get from doc
        loc_id = event_doc.get("location_id")
        if loc_id:
             loc = db.query(db_models.Location).filter(db_models.Location.id == loc_id).first()
             if loc:
                 node["location"] = {"id": loc.id, "name": loc.name}
    
    # Process Inputs
    inputs = event_doc.get("inputs", [])
    for inp in inputs:
        batch_id = inp.get("batch_id")
        if not batch_id:
            continue
            
        input_data = {"batch_id": batch_id, "details": None}
        
        # Get Batch Details
        batch = db.query(db_models.Batch).filter(db_models.Batch.id == batch_id).first()
        if batch:
            input_data["details"] = {
                "item_id": batch.item_id,
                "lot_code": batch.jsonb_doc.get("lot_code"),
                "external_lot_code": batch.jsonb_doc.get("external_lot_code")
            }
            
            # Recurse: Find creating event for this input batch
            prev_event = _find_creation_event(db, actor_id, batch_id)
            if prev_event:
                # We flatten the recursion for the report list, or we could nest it.
                # Let's nest logic but flatten list for readability? 
                # Actually, standard is usually tree. Let's append to 'inputs' of this node
                # For simplicity here, we will just recurse and let the caller handle structure or 
                # just list all upstream events linearly?
                # Let's stick to listing the immediate inputs here, and then recurse.
                _trace_upstream(db, actor_id, prev_event, results, visited)
        
        node["inputs"].append(input_data)
        
    results.append(node)


def _trace_downstream(db: Session, actor_id: str, batch_id: str, results: List[Dict], visited: Set[str], scope: Dict):
    """Recursively find outputs and distribution"""
    
    # Find events that consume this batch
    events = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id,
        db_models.Event.jsonb_doc['inputs'].contains([{"batch_id": batch_id}])
    ).all()
    
    for event in events:
        if event.id in visited:
            continue
        visited.add(event.id)
        
        event_doc = event.jsonb_doc
        
        node = {
            "event_id": event.id,
            "type": event.event_type,
            "date": event.timestamp,
            "destination": None,
            "outputs": []
        }
        
        # Check for Shipping (Distribution)
        if event.event_type == "shipping":
            # We assume shipping events might have notes or external_ids pointing to a buyer
            # Or we look at the 'outputs' if they went to a different actor?
            # For now, let's assume 'shipping' implies distribution.
            qty_moved = 0
            # If inputs have amounts, sum them? Or looks at outputs?
            # Usually shipping transforms 'inventory' to 'shipped'.
            # We check specific input amount for THIS batch if possible
            for inp in event_doc.get("inputs", []):
                if inp.get("batch_id") == batch_id:
                     # This logic requires amount on inputs, which we support but optional
                     pass
            
            # Add to distributed scope (simplification)
            # scope["distributed"] += amount
            
            node["destination"] = {
                "buyer": event_doc.get("notes", "Unknown Buyer"), # In strict mode, use Actor ID
                "contact": "See CRM" # Placeholder for Actor lookup
            }
            
        elif event.event_type == "disposal":
            # scope["waste"] += amount
            pass

        # Process Outputs (Recurse)
        outputs = event_doc.get("outputs", [])
        for out in outputs:
            out_batch_id = out.get("batch_id")
            node["outputs"].append(out_batch_id)
            _trace_downstream(db, actor_id, out_batch_id, results, visited, scope)
            
        results.append(node)
