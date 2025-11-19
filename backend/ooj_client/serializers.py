"""
Serialization utilities for converting between OOJ objects and JSON.
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, Union
from pathlib import Path
from .entities import Actor, Location, Item, Batch, Process, Event, Link


@dataclass
class RawEntity:
    """
    Fallback wrapper for unknown OOJ entity types.

    Used when `type` is not one of the core OOJ entities that this client
    knows about. Allows round-tripping arbitrary OOJ-compatible documents.
    """
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return self.data


EntityType = Union[Actor, Location, Item, Batch, Process, Event, Link, RawEntity]


def to_json(entity: EntityType, indent: int = 2) -> str:
    """Convert an OOJ entity to JSON string."""
    return json.dumps(entity.to_dict(), indent=indent)


def from_json(json_str: str) -> EntityType:
    """Parse JSON string into an OOJ entity."""
    data = json.loads(json_str)
    return from_dict(data)


def from_dict(data: Dict[str, Any]) -> EntityType:
    """
    Convert a dictionary to an OOJ entity.

    Known core types are converted to their dataclass equivalents.
    Unknown types are wrapped in RawEntity so they can be preserved
    and round-tripped without validation/interpretation.
    """
    entity_type = data.get("type")

    if entity_type == "actor":
        return Actor.from_dict(data)
    elif entity_type == "location":
        return Location.from_dict(data)
    elif entity_type == "item":
        return Item.from_dict(data)
    elif entity_type == "batch":
        return Batch.from_dict(data)
    elif entity_type == "process":
        return Process.from_dict(data)
    elif entity_type == "event":
        return Event.from_dict(data)
    elif entity_type == "link":
        return Link.from_dict(data)
    else:
        # Unknown or custom type (including x-*); keep it as-is
        return RawEntity(data=data)


def to_file(entity: EntityType, filepath: Union[str, Path], indent: int = 2) -> None:
    """Save an OOJ entity to a JSON file."""
    filepath = Path(filepath)
    with open(filepath, "w") as f:
        json.dump(entity.to_dict(), f, indent=indent)


def from_file(filepath: Union[str, Path]) -> EntityType:
    """Load an OOJ entity from a JSON file."""
    filepath = Path(filepath)
    with open(filepath, "r") as f:
        data = json.load(f)
    return from_dict(data)
