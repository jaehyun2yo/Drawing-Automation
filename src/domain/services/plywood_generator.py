"""Plywood frame generator service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.bounding_box import BoundingBox
from src.domain.types import PlateType, StandardColor, LineCategory

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


@dataclass(frozen=True, slots=True)
class PlywoodSettings:
    """Settings for plywood frame generation."""

    top_margin: float = 55.0
    bottom_margin: float = 25.0
    left_margin: float = 25.0
    right_margin: float = 25.0

    @classmethod
    def for_plate_type(cls, plate_type: PlateType) -> PlywoodSettings:
        """
        Create settings for a specific plate type.

        Args:
            plate_type: Type of plate (COPPER or AUTO)

        Returns:
            PlywoodSettings with appropriate margins
        """
        if plate_type == PlateType.COPPER:
            return cls(bottom_margin=25.0)
        elif plate_type == PlateType.AUTO:
            return cls(bottom_margin=15.0)
        else:
            return cls()


@dataclass
class PlywoodGenerator:
    """Service for generating plywood frame rectangles."""

    def generate_rectangle(self, bbox: BoundingBox) -> list[Line]:
        """
        Generate a rectangle of lines from a bounding box.

        Args:
            bbox: Bounding box defining the rectangle

        Returns:
            List of 4 lines forming the rectangle
        """
        # Define corner points
        bottom_left = Point(bbox.min_x, bbox.min_y)
        bottom_right = Point(bbox.max_x, bbox.min_y)
        top_right = Point(bbox.max_x, bbox.max_y)
        top_left = Point(bbox.min_x, bbox.max_y)

        # Create lines with plywood properties
        line_props = {
            'color': StandardColor.WHITE,
            'layer': 'PLYWOOD',
            'category': LineCategory.PLYWOOD,
        }

        lines = [
            # Bottom edge
            Line(start=bottom_left, end=bottom_right, **line_props),
            # Right edge
            Line(start=bottom_right, end=top_right, **line_props),
            # Top edge
            Line(start=top_right, end=top_left, **line_props),
            # Left edge
            Line(start=top_left, end=bottom_left, **line_props),
        ]

        return lines

    def apply_margins(
        self, bbox: BoundingBox, settings: PlywoodSettings
    ) -> BoundingBox:
        """
        Expand bounding box by margin amounts.

        Args:
            bbox: Original bounding box
            settings: Margin settings

        Returns:
            Expanded bounding box
        """
        return BoundingBox(
            min_x=bbox.min_x - settings.left_margin,
            min_y=bbox.min_y - settings.bottom_margin,
            max_x=bbox.max_x + settings.right_margin,
            max_y=bbox.max_y + settings.top_margin,
        )

    def generate_with_margins(
        self, bbox: BoundingBox, settings: PlywoodSettings
    ) -> list[Line]:
        """
        Generate plywood rectangle with margins applied.

        Args:
            bbox: Drawing bounding box
            settings: Margin settings

        Returns:
            List of lines forming the plywood frame
        """
        expanded = self.apply_margins(bbox, settings)
        return self.generate_rectangle(expanded)

    def generate_for_entities(
        self,
        entities: list[Entity],
        settings: PlywoodSettings | None = None
    ) -> list[Line]:
        """
        Generate plywood frame for a list of entities.

        Args:
            entities: List of drawing entities
            settings: Optional margin settings

        Returns:
            List of lines forming the plywood frame
        """
        if not entities:
            return []

        if settings is None:
            settings = PlywoodSettings()

        # Calculate bounding box
        from src.domain.services.geometry_service import GeometryService
        geometry = GeometryService()
        bbox = geometry.calculate_bounding_box(entities)

        if bbox is None:
            return []

        return self.generate_with_margins(bbox, settings)

    def calculate_drawing_position(
        self, drawing_bbox: BoundingBox, settings: PlywoodSettings
    ) -> Point:
        """
        Calculate the offset to position drawing within plywood margins.

        The drawing is positioned such that the specified margins
        are maintained on all sides.

        Args:
            drawing_bbox: Bounding box of the drawing
            settings: Margin settings

        Returns:
            Point representing offset to apply to drawing
        """
        # Calculate where drawing's min corner should be relative to plywood
        target_min_x = 0  # Drawing min_x stays at 0, plywood extends left
        target_min_y = 0  # Drawing min_y stays at 0, plywood extends down

        # Calculate offset needed
        dx = target_min_x - drawing_bbox.min_x
        dy = target_min_y - drawing_bbox.min_y

        return Point(drawing_bbox.min_x + dx, drawing_bbox.min_y + dy)
