"""
BoundingBox entity representing a rectangular area.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from src.domain.entities.point import Point


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """
    Immutable axis-aligned bounding box.

    Attributes:
        min_x: Minimum X coordinate
        min_y: Minimum Y coordinate
        max_x: Maximum X coordinate
        max_y: Maximum Y coordinate
    """

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        """Width of the bounding box."""
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        """Height of the bounding box."""
        return self.max_y - self.min_y

    @property
    def center(self) -> Point:
        """Center point of the bounding box."""
        from src.domain.entities.point import Point
        return Point(
            x=(self.min_x + self.max_x) / 2,
            y=(self.min_y + self.max_y) / 2
        )

    def contains_point(self, point: Point) -> bool:
        """
        Check if the bounding box contains a point.

        Args:
            point: The point to check

        Returns:
            True if the point is inside or on the edge of the bounding box
        """
        return (
            self.min_x <= point.x <= self.max_x and
            self.min_y <= point.y <= self.max_y
        )

    def expand(self, margin: float) -> BoundingBox:
        """
        Create a new bounding box expanded by a margin.

        Args:
            margin: The margin to expand by (can be negative to shrink)

        Returns:
            New BoundingBox expanded by the margin
        """
        return BoundingBox(
            min_x=self.min_x - margin,
            min_y=self.min_y - margin,
            max_x=self.max_x + margin,
            max_y=self.max_y + margin
        )

    def union(self, other: BoundingBox) -> BoundingBox:
        """
        Create a new bounding box that contains both bounding boxes.

        Args:
            other: The other bounding box

        Returns:
            New BoundingBox containing both
        """
        return BoundingBox(
            min_x=min(self.min_x, other.min_x),
            min_y=min(self.min_y, other.min_y),
            max_x=max(self.max_x, other.max_x),
            max_y=max(self.max_y, other.max_y)
        )

    def is_completely_outside(self, other: BoundingBox) -> bool:
        """
        Check if this bounding box is completely outside another.

        Args:
            other: The other bounding box

        Returns:
            True if completely outside (no overlap)
        """
        return (
            self.max_x < other.min_x or
            self.min_x > other.max_x or
            self.max_y < other.min_y or
            self.min_y > other.max_y
        )

    @classmethod
    def from_points(cls, points: Sequence[Point]) -> BoundingBox:
        """
        Create a bounding box from a sequence of points.

        Args:
            points: Sequence of points

        Returns:
            New BoundingBox containing all points

        Raises:
            ValueError: If points sequence is empty
        """
        if not points:
            raise ValueError("Cannot create bounding box from empty points")

        min_x = min(p.x for p in points)
        min_y = min(p.y for p in points)
        max_x = max(p.x for p in points)
        max_y = max(p.y for p in points)

        return cls(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)

    def __repr__(self) -> str:
        return (
            f"BoundingBox(min=({self.min_x:.3f}, {self.min_y:.3f}), "
            f"max=({self.max_x:.3f}, {self.max_y:.3f}))"
        )
