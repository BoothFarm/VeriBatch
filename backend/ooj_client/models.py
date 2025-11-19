"""
Common data models used across OOJ entities.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any


@dataclass
class Quantity:
    """Represents a quantity with amount and unit."""
    
    amount: float
    unit: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {"amount": self.amount, "unit": self.unit}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quantity":
        return cls(amount=data["amount"], unit=data["unit"])


@dataclass
class Attachment:
    """Represents an attachment (photo, document, certificate, etc.)."""
    
    type: str
    url: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: Optional[str] = None
    hash: Optional[str] = None
    
    VALID_TYPES = {
        "photo", "document", "certificate", "test_result", 
        "label", "video", "other"
    }

    def __post_init__(self):
        if self.type not in self.VALID_TYPES and not self.type.startswith("x-"):
            raise ValueError(f"Invalid attachment type: {self.type}")

    
    def to_dict(self) -> Dict[str, Any]:
        data = {"type": self.type, "url": self.url}
        if self.description:
            data["description"] = self.description
        if self.mime_type:
            data["mime_type"] = self.mime_type
        if self.created_at:
            data["created_at"] = self.created_at
        if self.hash:
            data["hash"] = self.hash
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attachment":
        return cls(
            type=data["type"],
            url=data["url"],
            description=data.get("description"),
            mime_type=data.get("mime_type"),
            created_at=data.get("created_at"),
            hash=data.get("hash")
        )


@dataclass
class ExternalIds:
    """Container for external system identifiers."""
    
    ids: Dict[str, str] = field(default_factory=dict)
    
    def add(self, system: str, identifier: str) -> None:
        """Add an external ID."""
        self.ids[system] = identifier
    
    def get(self, system: str) -> Optional[str]:
        """Get an external ID."""
        return self.ids.get(system)
    
    def to_dict(self) -> Dict[str, str]:
        return self.ids.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ExternalIds":
        return cls(ids=data.copy())
    
    def __bool__(self) -> bool:
        return bool(self.ids)




@dataclass
class BatchInput:
    """Represents an input batch in an Event."""
    
    batch_id: str
    amount: Quantity
    actor_id: Optional[str] = None  # optional cross-actor reference
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "batch_id": self.batch_id,
            "amount": self.amount.to_dict(),
        }
        if self.actor_id:
            data["actor_id"] = self.actor_id
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchInput":
        return cls(
            batch_id=data["batch_id"],
            amount=Quantity.from_dict(data["amount"]),
            actor_id=data.get("actor_id"),
        )


@dataclass
class BatchOutput:
    """Represents an output batch in an Event."""
    
    batch_id: str
    amount: Quantity
    actor_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "batch_id": self.batch_id,
            "amount": self.amount.to_dict(),
        }
        if self.actor_id:
            data["actor_id"] = self.actor_id
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchOutput":
        return cls(
            batch_id=data["batch_id"],
            amount=Quantity.from_dict(data["amount"]),
            actor_id=data.get("actor_id"),
        )

