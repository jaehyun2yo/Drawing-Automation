"""
Point entity representing a 2D coordinate.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.types import Coordinates2D


@dataclass(frozen=True, slots=True)
class Point:
    """
    Immutable 2D point representing a coordinate in the drawing space.

    Attributes:
        x: X coordinate in millimeters
        y: Y coordinate in millimeters
    """

    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        """
        Calculate the Euclidean distance to another point.

        Args:
            other: The other point to calculate distance to

        Returns:
            Distance in millimeters
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def midpoint_to(self, other: Point) -> Point:
        """
        Calculate the midpoint between this point and another.

        Args:
            other: The other point

        Returns:
            New Point at the midpoint
        """
        return Point(
            x=(self.x + other.x) / 2,
            y=(self.y + other.y) / 2
        )

    def mirror_x(self, center_x: float) -> Point:
        """
        Mirror this point across a vertical axis.

        Args:
            center_x: X coordinate of the mirror axis

        Returns:
            New Point mirrored across the axis
        """
        return Point(
            x=2 * center_x - self.x,
            y=self.y
        )

    def translate(self, dx: float, dy: float) -> Point:
        """
        Translate this point by the given offset.

        Args:
            dx: X offset in millimeters
            dy: Y offset in millimeters

        Returns:
            New Point translated by the offset
        """
        return Point(
            x=self.x + dx,
            y=self.y + dy
        )

    def to_tuple(self) -> Coordinates2D:
        """
        Convert point to a tuple of coordinates.

        Returns:
            Tuple of (x, y) coordinates
        """
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, coords: Coordinates2D) -> Point:
        """
        Create a Point from a tuple of coordinates.

        Args:
            coords: Tuple of (x, y) coordinates

        Returns:
            New Point instance
        """
        return cls(x=coords[0], y=coords[1])

    def __repr__(self) -> str:
        return f"Point({self.x:.3f}, {self.y:.3f})"
