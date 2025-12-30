"""
Line entity representing a straight line segment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from src.domain.entities.entity import Entity
from src.domain.entities.point import Point
from src.domain.entities.bounding_box import BoundingBox
from src.domain.types import EntityType, LineCategory, ACIColor, StandardColor

if TYPE_CHECKING:
    pass


@dataclass
class Line(Entity):
    """
    A straight line segment defined by start and end points.

    Attributes:
        start: Starting point of the line
        end: Ending point of the line
    """

    start: Point = field(default_factory=lambda: Point(0.0, 0.0))
    end: Point = field(default_factory=lambda: Point(0.0, 0.0))

    # Inherited from Entity
    id: UUID = field(default_factory=uuid4, compare=False)
    layer: str = field(default="0")
    color: ACIColor = field(default=StandardColor.WHITE)
    linetype: str = field(default="CONTINUOUS")
    category: LineCategory = field(default=LineCategory.UNKNOWN)

    @property
    def entity_type(self) -> EntityType:
        """Return LINE entity type."""
        return EntityType.LINE

    @property
    def length(self) -> float:
        """Calculate the length of the line."""
        return self.start.distance_to(self.end)

    @property
    def midpoint(self) -> Point:
        """Get the midpoint of the line."""
        return self.start.midpoint_to(self.end)

    @property
    def bounding_box(self) -> BoundingBox:
        """Calculate the bounding box of the line."""
        return BoundingBox(
            min_x=min(self.start.x, self.end.x),
            min_y=min(self.start.y, self.end.y),
            max_x=max(self.start.x, self.end.x),
            max_y=max(self.start.y, self.end.y)
        )

    def is_horizontal(self, tolerance: float = 0.001) -> bool:
        """
        Check if the line is horizontal (parallel to X axis).

        Args:
            tolerance: Maximum allowed Y difference

        Returns:
            True if the line is horizontal within tolerance
        """
        return abs(self.start.y - self.end.y) <= tolerance

    def is_vertical(self, tolerance: float = 0.001) -> bool:
        """
        Check if the line is vertical (parallel to Y axis).

        Args:
            tolerance: Maximum allowed X difference

        Returns:
            True if the line is vertical within tolerance
        """
        return abs(self.start.x - self.end.x) <= tolerance

    def point_at_ratio(self, ratio: float) -> Point:
        """
        Get a point along the line at a specific ratio.

        Args:
            ratio: Position along the line (0.0 = start, 1.0 = end)

        Returns:
            Point at the specified ratio
        """
        return Point(
            x=self.start.x + (self.end.x - self.start.x) * ratio,
            y=self.start.y + (self.end.y - self.start.y) * ratio
        )

    def split_at_ratios(self, ratios: list[float]) -> list[Line]:
        """
        Split the line into segments at the specified ratios.

        Args:
            ratios: List of ratios where to split (between 0 and 1)

        Returns:
            List of Line segments
        """
        # Ensure ratios are sorted and include 0 and 1
        all_ratios = sorted(set([0.0] + ratios + [1.0]))

        segments: list[Line] = []
        for i in range(len(all_ratios) - 1):
            start_point = self.point_at_ratio(all_ratios[i])
            end_point = self.point_at_ratio(all_ratios[i + 1])
            segment = Line(
                start=start_point,
                end=end_point,
                layer=self.layer,
                color=self.color,
                linetype=self.linetype,
                category=self.category
            )
            segments.append(segment)

        return segments

    def mirror_x(self, center_x: float) -> Line:
        """
        Create a new line mirrored across a vertical axis.

        Args:
            center_x: X coordinate of the mirror axis

        Returns:
            New Line mirrored across the axis
        """
        return Line(
            start=self.start.mirror_x(center_x),
            end=self.end.mirror_x(center_x),
            layer=self.layer,
            color=self.color,
            linetype=self.linetype,
            category=self.category
        )

    def translate(self, dx: float, dy: float) -> Line:
        """
        Create a new line translated by the given offset.

        Args:
            dx: X offset in millimeters
            dy: Y offset in millimeters

        Returns:
            New Line translated by the offset
        """
        return Line(
            start=self.start.translate(dx, dy),
            end=self.end.translate(dx, dy),
            layer=self.layer,
            color=self.color,
            linetype=self.linetype,
            category=self.category
        )

    def __repr__(self) -> str:
        return f"Line({self.start} -> {self.end}, len={self.length:.3f})"
