"""
Core OOJ entity classes.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .models import Quantity, Attachment, ExternalIds, BatchInput, BatchOutput


SCHEMA_VERSION = "open-origin-json/0.4"


@dataclass
class Actor:
    """Represents an organization or person responsible for production."""
    
    id: str
    name: str
    kind: Optional[str] = None
    contacts: Optional[Dict[str, str]] = None
    address: Optional[Dict[str, str]] = None
    certifications: List[str] = field(default_factory=list)
    external_ids: Optional[ExternalIds] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "schema": SCHEMA_VERSION,
            "type": "actor",
            "id": self.id,
            "name": self.name
        }
        if self.kind:
            data["kind"] = self.kind
        if self.contacts:
            data["contacts"] = self.contacts
        if self.address:
            data["address"] = self.address
        if self.certifications:
            data["certifications"] = self.certifications
        if self.external_ids:
            data["external_ids"] = self.external_ids.to_dict()
        if self.created_at:
            data["created_at"] = self.created_at
        if self.updated_at:
            data["updated_at"] = self.updated_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Actor":
        return cls(
            id=data["id"],
            name=data["name"],
            kind=data.get("kind"),
            contacts=data.get("contacts"),
            address=data.get("address"),
            certifications=data.get("certifications", []),
            external_ids=ExternalIds.from_dict(data["external_ids"]) if "external_ids" in data else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class Location:
    """Represents a physical or logical place."""
    
    id: str
    actor_id: str
    name: str
    kind: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    address: Optional[Dict[str, str]] = None
    external_ids: Optional[ExternalIds] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "schema": SCHEMA_VERSION,
            "type": "location",
            "id": self.id,
            "actor_id": self.actor_id,
            "name": self.name
        }
        if self.kind:
            data["kind"] = self.kind
        if self.coordinates:
            data["coordinates"] = self.coordinates
        if self.address:
            data["address"] = self.address
        if self.external_ids:
            data["external_ids"] = self.external_ids.to_dict()
        if self.created_at:
            data["created_at"] = self.created_at
        if self.updated_at:
            data["updated_at"] = self.updated_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        return cls(
            id=data["id"],
            actor_id=data["actor_id"],
            name=data["name"],
            kind=data.get("kind"),
            coordinates=data.get("coordinates"),
            address=data.get("address"),
            external_ids=ExternalIds.from_dict(data["external_ids"]) if "external_ids" in data else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class Item:
    """Represents a type of thing: ingredient, product, or packaging."""
    
    id: str
    actor_id: str
    name: str
    category: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    external_ids: Optional[ExternalIds] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "schema": SCHEMA_VERSION,
            "type": "item",
            "id": self.id,
            "actor_id": self.actor_id,
            "name": self.name
        }
        if self.category:
            data["category"] = self.category
        if self.unit:
            data["unit"] = self.unit
        if self.description:
            data["description"] = self.description
        if self.external_ids:
            data["external_ids"] = self.external_ids.to_dict()
        if self.created_at:
            data["created_at"] = self.created_at
        if self.updated_at:
            data["updated_at"] = self.updated_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        return cls(
            id=data["id"],
            actor_id=data["actor_id"],
            name=data["name"],
            category=data.get("category"),
            unit=data.get("unit"),
            description=data.get("description"),
            external_ids=ExternalIds.from_dict(data["external_ids"]) if "external_ids" in data else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class Batch:
    """Represents the smallest traceable unit of an item."""
    
    id: str
    actor_id: str
    item_id: str
    location_id: Optional[str] = None
    quantity: Optional[Quantity] = None
    status: str = "active"
    origin_kind: Optional[str] = None
    production_date: Optional[str] = None
    expiration_date: Optional[str] = None
    best_before_date: Optional[str] = None
    external_ids: Optional[ExternalIds] = None
    attachments: List[Attachment] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    VALID_STATUSES = {
        "active", "depleted", "quarantined", 
        "recalled", "expired", "disposed"
    }
    
    def __post_init__(self):
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "schema": SCHEMA_VERSION,
            "type": "batch",
            "id": self.id,
            "actor_id": self.actor_id,
            "item_id": self.item_id
        }
        if self.location_id:
            data["location_id"] = self.location_id
        if self.quantity:
            data["quantity"] = self.quantity.to_dict()
        if self.status != "active":
            data["status"] = self.status
        if self.origin_kind:
            data["origin_kind"] = self.origin_kind
        if self.production_date:
            data["production_date"] = self.production_date
        if self.expiration_date:
            data["expiration_date"] = self.expiration_date
        if self.best_before_date:
            data["best_before_date"] = self.best_before_date
        if self.external_ids:
            data["external_ids"] = self.external_ids.to_dict()
        if self.attachments:
            data["attachments"] = [a.to_dict() for a in self.attachments]
        if self.created_at:
            data["created_at"] = self.created_at
        if self.updated_at:
            data["updated_at"] = self.updated_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Batch":
        return cls(
            id=data["id"],
            actor_id=data["actor_id"],
            item_id=data["item_id"],
            location_id=data.get("location_id"),
            quantity=Quantity.from_dict(data["quantity"]) if "quantity" in data else None,
            status=data.get("status", "active"),
            origin_kind=data.get("origin_kind"),
            production_date=data.get("production_date"),
            expiration_date=data.get("expiration_date"),
            best_before_date=data.get("best_before_date"),
            external_ids=ExternalIds.from_dict(data["external_ids"]) if "external_ids" in data else None,
            attachments=[Attachment.from_dict(a) for a in data.get("attachments", [])],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class Process:
    """Represents a defined recipe or procedure."""
    
    id: str
    actor_id: str
    name: str
    kind: Optional[str] = None
    version: Optional[str] = None
    steps: List[str] = field(default_factory=list)
    inputs: Optional[List[Dict[str, Any]]] = None
    outputs: Optional[List[Dict[str, Any]]] = None
    attachments: List[Attachment] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "schema": SCHEMA_VERSION,
            "type": "process",
            "id": self.id,
            "actor_id": self.actor_id,
            "name": self.name
        }
        if self.kind:
            data["kind"] = self.kind
        if self.version:
            data["version"] = self.version
        if self.steps:
            data["steps"] = self.steps
        if self.inputs:
            data["inputs"] = self.inputs
        if self.outputs:
            data["outputs"] = self.outputs
        if self.attachments:
            data["attachments"] = [a.to_dict() for a in self.attachments]
        if self.created_at:
            data["created_at"] = self.created_at
        if self.updated_at:
            data["updated_at"] = self.updated_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Process":
        return cls(
            id=data["id"],
            actor_id=data["actor_id"],
            name=data["name"],
            kind=data.get("kind"),
            version=data.get("version"),
            steps=data.get("steps", []),
            inputs=data.get("inputs"),
            outputs=data.get("outputs"),
            attachments=[Attachment.from_dict(a) for a in data.get("attachments", [])],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class Event:
    """Represents a timestamped action that transforms or moves goods."""
    
    id: str
    actor_id: str
    timestamp: str
    event_type: str
    location_id: Optional[str] = None
    process_id: Optional[str] = None
    inputs: List[BatchInput] = field(default_factory=list)
    outputs: List[BatchOutput] = field(default_factory=list)
    packaging_materials: List[BatchInput] = field(default_factory=list)
    notes: Optional[str] = None
    performed_by: Optional[str] = None
    external_ids: Optional[ExternalIds] = None
    attachments: List[Attachment] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    VALID_EVENT_TYPES = {
        "harvest", "processing", "packaging", "receiving",
        "shipping", "storage_move", "quality_check",
        "split", "merge", "disposal",
    }

    def __post_init__(self):
        if (
            self.event_type not in self.VALID_EVENT_TYPES
            and not self.event_type.startswith("x-")
        ):
            raise ValueError(f"Invalid event_type: {self.event_type}")

    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "schema": SCHEMA_VERSION,
            "type": "event",
            "id": self.id,
            "actor_id": self.actor_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type
        }
        if self.location_id:
            data["location_id"] = self.location_id
        if self.process_id:
            data["process_id"] = self.process_id
        if self.inputs:
            data["inputs"] = [i.to_dict() for i in self.inputs]
        if self.outputs:
            data["outputs"] = [o.to_dict() for o in self.outputs]
        if self.packaging_materials:
            data["packaging_materials"] = [p.to_dict() for p in self.packaging_materials]
        if self.notes:
            data["notes"] = self.notes
        if self.performed_by:
            data["performed_by"] = self.performed_by
        if self.external_ids:
            data["external_ids"] = self.external_ids.to_dict()
        if self.attachments:
            data["attachments"] = [a.to_dict() for a in self.attachments]
        if self.created_at:
            data["created_at"] = self.created_at
        if self.updated_at:
            data["updated_at"] = self.updated_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            id=data["id"],
            actor_id=data["actor_id"],
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            location_id=data.get("location_id"),
            process_id=data.get("process_id"),
            inputs=[BatchInput.from_dict(i) for i in data.get("inputs", [])],
            outputs=[BatchOutput.from_dict(o) for o in data.get("outputs", [])],
            packaging_materials=[BatchInput.from_dict(p) for p in data.get("packaging_materials", [])],
            notes=data.get("notes"),
            performed_by=data.get("performed_by"),
            external_ids=ExternalIds.from_dict(data["external_ids"]) if "external_ids" in data else None,
            attachments=[Attachment.from_dict(a) for a in data.get("attachments", [])],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class Link:
    """Represents an explicit relationship between entities."""
    
    id: str
    actor_id: str
    kind: str
    from_batch_id: Optional[str] = None
    to_batch_id: Optional[str] = None
    from_entity_id: Optional[str] = None
    to_entity_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "schema": SCHEMA_VERSION,
            "type": "link",
            "id": self.id,
            "actor_id": self.actor_id,
            "kind": self.kind
        }
        if self.from_batch_id:
            data["from_batch_id"] = self.from_batch_id
        if self.to_batch_id:
            data["to_batch_id"] = self.to_batch_id
        if self.from_entity_id:
            data["from_entity_id"] = self.from_entity_id
        if self.to_entity_id:
            data["to_entity_id"] = self.to_entity_id
        if self.metadata:
            data["metadata"] = self.metadata
        if self.created_at:
            data["created_at"] = self.created_at
        if self.updated_at:
            data["updated_at"] = self.updated_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Link":
        return cls(
            id=data["id"],
            actor_id=data["actor_id"],
            kind=data["kind"],
            from_batch_id=data.get("from_batch_id"),
            to_batch_id=data.get("to_batch_id"),
            from_entity_id=data.get("from_entity_id"),
            to_entity_id=data.get("to_entity_id"),
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
