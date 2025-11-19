"""
Validation utilities for OOJ entities.
"""

from typing import Dict, Any, List


class ValidationError(Exception):
    """Raised when entity validation fails."""
    pass


def validate_entity(data: Dict[str, Any]) -> List[str]:
    """
    Validate an OOJ entity dictionary.
    
    Returns a list of validation errors (empty if valid).
    """
    errors = []
    
    # Check required fields
    if "schema" not in data:
        errors.append("Missing required field: schema")
    else:
        schema = data["schema"]
        if not isinstance(schema, str) or not schema.startswith("open-origin-json/"):
            errors.append(f"Invalid schema value: {schema}")

    
    if "type" not in data:
        errors.append("Missing required field: type")
    else:
        entity_type = data["type"]
        
        # Validate based on entity type
        if entity_type == "actor":
            errors.extend(_validate_actor(data))
        elif entity_type == "location":
            errors.extend(_validate_location(data))
        elif entity_type == "item":
            errors.extend(_validate_item(data))
        elif entity_type == "batch":
            errors.extend(_validate_batch(data))
        elif entity_type == "process":
            errors.extend(_validate_process(data))
        elif entity_type == "event":
            errors.extend(_validate_event(data))
        elif entity_type == "link":
            errors.extend(_validate_link(data))
        else:
            # Unknown types are allowed by the spec; we just don't validate them
            # and do not treat them as an error here.
            pass
    
    return errors


def _validate_actor(data: Dict[str, Any]) -> List[str]:
    errors = []
    if "id" not in data:
        errors.append("Actor missing required field: id")
    if "name" not in data:
        errors.append("Actor missing required field: name")
    return errors


def _validate_location(data: Dict[str, Any]) -> List[str]:
    errors = []
    if "id" not in data:
        errors.append("Location missing required field: id")
    if "actor_id" not in data:
        errors.append("Location missing required field: actor_id")
    if "name" not in data:
        errors.append("Location missing required field: name")
    return errors


def _validate_item(data: Dict[str, Any]) -> List[str]:
    errors = []
    if "id" not in data:
        errors.append("Item missing required field: id")
    if "actor_id" not in data:
        errors.append("Item missing required field: actor_id")
    if "name" not in data:
        errors.append("Item missing required field: name")
    return errors


def _validate_batch(data: Dict[str, Any]) -> List[str]:
    errors = []
    if "id" not in data:
        errors.append("Batch missing required field: id")
    if "actor_id" not in data:
        errors.append("Batch missing required field: actor_id")
    if "item_id" not in data:
        errors.append("Batch missing required field: item_id")
    
    if "status" in data:
        valid_statuses = {"active", "depleted", "quarantined", "recalled", "expired", "disposed"}
        if data["status"] not in valid_statuses:
            errors.append(f"Invalid batch status: {data['status']}")
    
    if "quantity" in data:
        if not isinstance(data["quantity"], dict):
            errors.append("Batch quantity must be an object")
        elif "amount" not in data["quantity"] or "unit" not in data["quantity"]:
            errors.append("Batch quantity must have 'amount' and 'unit' fields")
    
    return errors


def _validate_process(data: Dict[str, Any]) -> List[str]:
    errors = []
    if "id" not in data:
        errors.append("Process missing required field: id")
    if "actor_id" not in data:
        errors.append("Process missing required field: actor_id")
    if "name" not in data:
        errors.append("Process missing required field: name")
    return errors


def _validate_event(data: Dict[str, Any]) -> List[str]:
    errors = []
    if "id" not in data:
        errors.append("Event missing required field: id")
    if "actor_id" not in data:
        errors.append("Event missing required field: actor_id")
    if "timestamp" not in data:
        errors.append("Event missing required field: timestamp")
    if "event_type" not in data:
        errors.append("Event missing required field: event_type")
    else:
        valid_types = {
            "harvest", "processing", "packaging", "receiving",
            "shipping", "storage_move", "quality_check",
            "split", "merge", "disposal",
        }
        event_type = data["event_type"]
        if event_type not in valid_types and not event_type.startswith("x-"):
            errors.append(f"Invalid event_type: {event_type}")

    
    return errors


def _validate_link(data: Dict[str, Any]) -> List[str]:
    errors = []
    if "id" not in data:
        errors.append("Link missing required field: id")
    if "actor_id" not in data:
        errors.append("Link missing required field: actor_id")
    if "kind" not in data:
        errors.append("Link missing required field: kind")
    return errors
