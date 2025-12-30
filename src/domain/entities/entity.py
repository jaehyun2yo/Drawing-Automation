"""
Base Entity class for all DXF entities.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from src.domain.types import EntityType, LineCategory, ACIColor, StandardColor

if TYPE_CHECKING:
    from src.domain.entities.bounding_box import BoundingBox
    from src.domain.entities.point import Point


@dataclass
class Entity(ABC):
    """
    Abstract base class for all DXF entities.

    Attributes:
        id: Unique identifier for the entity
        layer: Layer name the entity belongs to
        color: AutoCAD Color Index
        linetype: Line type name
        category: Classification category (CUT, CREASE, etc.)
    """

    id: UUID = field(default_factory=uuid4, compare=False)
    layer: str = field(default="0")
    color: ACIColor = field(default=StandardColor.WHITE)
    linetype: str = field(default="CONTINUOUS")
    category: LineCategory = field(default=LineCategory.UNKNOWN)

    @property
    @abstractmethod
    def entity_type(self) -> EntityType:
        """Return the type of this entity."""
        ...

    @property
    @abstractmethod
    def bounding_box(self) -> BoundingBox:
        """Calculate and return the bounding box of this entity."""
        ...

    @abstractmethod
    def mirror_x(self, center_x: float) -> Entity:
        """
        Create a new entity mirrored across a vertical axis.

        Args:
            center_x: X coordinate of the mirror axis

        Returns:
            New entity mirrored across the axis
        """
        ...

    @abstractmethod
    def translate(self, dx: float, dy: float) -> Entity:
        """
        Create a new entity translated by the given offset.

        Args:
            dx: X offset in millimeters
            dy: Y offset in millimeters

        Returns:
            New entity translated by the offset
        """
        ...
