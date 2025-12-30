"""
Arc entity representing a circular arc.
"""
from __future__ import annotations

import math
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
class Arc(Entity):
    """
    A circular arc defined by center, radius, and angles.

    Attributes:
        center: Center point of the arc
        radius: Radius of the arc in millimeters
        start_angle: Starting angle in degrees (0 = positive X axis)
        end_angle: Ending angle in degrees
    """

    center: Point = field(default_factory=lambda: Point(0.0, 0.0))
    radius: float = field(default=0.0)
    start_angle: float = field(default=0.0)
    end_angle: float = field(default=360.0)

    # Inherited from Entity
    id: UUID = field(default_factory=uuid4, compare=False)
    layer: str = field(default="0")
    color: ACIColor = field(default=StandardColor.WHITE)
    linetype: str = field(default="CONTINUOUS")
    category: LineCategory = field(default=LineCategory.UNKNOWN)

    @property
    def entity_type(self) -> EntityType:
        """Return ARC entity type."""
        return EntityType.ARC

    @property
    def start_point(self) -> Point:
        """Calculate the start point of the arc."""
        angle_rad = math.radians(self.start_angle)
        return Point(
            x=self.center.x + self.radius * math.cos(angle_rad),
            y=self.center.y + self.radius * math.sin(angle_rad)
        )

    @property
    def end_point(self) -> Point:
        """Calculate the end point of the arc."""
        angle_rad = math.radians(self.end_angle)
        return Point(
            x=self.center.x + self.radius * math.cos(angle_rad),
            y=self.center.y + self.radius * math.sin(angle_rad)
        )

    @property
    def bounding_box(self) -> BoundingBox:
        """
        Calculate the bounding box of the arc.

        This considers the arc's sweep and includes any extrema
        (0, 90, 180, 270 degrees) that fall within the arc.
        """
        # Start with the endpoints
        points = [self.start_point, self.end_point]

        # Normalize angles to 0-360 range
        start = self.start_angle % 360
        end = self.end_angle % 360

        # Check if arc crosses each cardinal direction
        def angle_in_arc(angle: float) -> bool:
            """Check if an angle falls within the arc."""
            if start <= end:
                return start <= angle <= end
            else:
                # Arc crosses 0 degrees
                return angle >= start or angle <= end

        # Add extrema points if they're in the arc
        if angle_in_arc(0):
            points.append(Point(self.center.x + self.radius, self.center.y))
        if angle_in_arc(90):
            points.append(Point(self.center.x, self.center.y + self.radius))
        if angle_in_arc(180):
            points.append(Point(self.center.x - self.radius, self.center.y))
        if angle_in_arc(270):
            points.append(Point(self.center.x, self.center.y - self.radius))

        return BoundingBox.from_points(points)

    def mirror_x(self, center_x: float) -> Arc:
        """
        Create a new arc mirrored across a vertical axis.

        Args:
            center_x: X coordinate of the mirror axis

        Returns:
            New Arc mirrored across the axis
        """
        # Mirror the center point
        new_center = self.center.mirror_x(center_x)

        # Mirror the angles (reflect across Y axis)
        # When mirroring, angles are reflected: angle -> 180 - angle
        new_start_angle = 180 - self.end_angle
        new_end_angle = 180 - self.start_angle

        return Arc(
            center=new_center,
            radius=self.radius,
            start_angle=new_start_angle,
            end_angle=new_end_angle,
            layer=self.layer,
            color=self.color,
            linetype=self.linetype,
            category=self.category
        )

    def translate(self, dx: float, dy: float) -> Arc:
        """
        Create a new arc translated by the given offset.

        Args:
            dx: X offset in millimeters
            dy: Y offset in millimeters

        Returns:
            New Arc translated by the offset
        """
        return Arc(
            center=self.center.translate(dx, dy),
            radius=self.radius,
            start_angle=self.start_angle,
            end_angle=self.end_angle,
            layer=self.layer,
            color=self.color,
            linetype=self.linetype,
            category=self.category
        )

    def __repr__(self) -> str:
        return (
            f"Arc(center={self.center}, r={self.radius:.3f}, "
            f"angles={self.start_angle:.1f}°-{self.end_angle:.1f}°)"
        )
