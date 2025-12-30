"""Service for generating straight knife lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.bounding_box import BoundingBox
from src.domain.types import LineCategory, StandardColor
from src.domain.value_objects.bridge_settings import BridgeSettings
from src.domain.services.bridge_calculator import BridgeCalculator

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class StraightKnifeSettings:
    """Settings for straight knife generation."""

    apply_bridges: bool = True
    bridge_settings: BridgeSettings = field(default_factory=BridgeSettings.for_cut)
    color: int = StandardColor.RED
    layer: str = "CUT"


@dataclass
class StraightKnifeGenerator:
    """
    Service for generating straight knife lines.

    Straight knives are extension lines added to the left and right
    of the drawing to extend to the plywood edges. They are used when
    the drawing doesn't span the full width of the paper.
    """

    def generate(
        self,
        drawing_bbox: BoundingBox,
        plywood_bbox: BoundingBox,
        y_positions: list[float] | None = None,
        settings: StraightKnifeSettings | None = None
    ) -> list[Line]:
        """
        Generate straight knife lines.

        Args:
            drawing_bbox: Bounding box of the drawing
            plywood_bbox: Bounding box of the plywood frame
            y_positions: Y coordinates for straight knives (default: center)
            settings: Straight knife settings

        Returns:
            List of Line entities for straight knives
        """
        if settings is None:
            settings = StraightKnifeSettings()

        # Default to center Y if no positions specified
        if y_positions is None:
            center_y = (drawing_bbox.min_y + drawing_bbox.max_y) / 2
            y_positions = [center_y]

        knives = []

        for y in y_positions:
            # Generate left knife (from plywood left edge to drawing left edge)
            left_knives = self._generate_knife(
                start_x=plywood_bbox.min_x,
                end_x=drawing_bbox.min_x,
                y=y,
                settings=settings
            )
            knives.extend(left_knives)

            # Generate right knife (from drawing right edge to plywood right edge)
            right_knives = self._generate_knife(
                start_x=drawing_bbox.max_x,
                end_x=plywood_bbox.max_x,
                y=y,
                settings=settings
            )
            knives.extend(right_knives)

        return knives

    def generate_at_center(
        self,
        drawing_bbox: BoundingBox,
        plywood_bbox: BoundingBox,
        settings: StraightKnifeSettings | None = None
    ) -> list[Line]:
        """
        Generate straight knife at drawing center Y.

        Args:
            drawing_bbox: Bounding box of the drawing
            plywood_bbox: Bounding box of the plywood frame
            settings: Straight knife settings

        Returns:
            List of Line entities for straight knives
        """
        center_y = (drawing_bbox.min_y + drawing_bbox.max_y) / 2
        return self.generate(drawing_bbox, plywood_bbox, [center_y], settings)

    def find_horizontal_line_positions(
        self,
        entities: list,
        tolerance: float = 1.0
    ) -> list[float]:
        """
        Find Y positions of major horizontal lines in the drawing.

        This can be used to place straight knives at natural cut lines
        instead of arbitrary positions.

        Args:
            entities: List of entities to analyze
            tolerance: Tolerance for grouping similar Y positions

        Returns:
            List of Y positions where horizontal lines exist
        """
        from src.domain.entities.line import Line

        # Collect Y positions of horizontal lines
        y_positions = []

        for entity in entities:
            if isinstance(entity, Line):
                # Check if line is horizontal (same Y for start and end)
                if abs(entity.start.y - entity.end.y) < tolerance:
                    y_positions.append(entity.start.y)

        # Cluster similar Y positions
        if not y_positions:
            return []

        y_positions.sort()
        clusters = []
        current_cluster = [y_positions[0]]

        for y in y_positions[1:]:
            if y - current_cluster[-1] <= tolerance:
                current_cluster.append(y)
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [y]

        if current_cluster:
            clusters.append(sum(current_cluster) / len(current_cluster))

        return clusters

    def _generate_knife(
        self,
        start_x: float,
        end_x: float,
        y: float,
        settings: StraightKnifeSettings
    ) -> list[Line]:
        """
        Generate a single knife line (possibly split by bridges).

        Args:
            start_x: Starting X coordinate
            end_x: Ending X coordinate
            y: Y coordinate
            settings: Knife settings

        Returns:
            List of Line segments (split by bridges if applicable)
        """
        # Skip if start and end are same or very close
        length = abs(end_x - start_x)
        if length < 1.0:
            return []

        base_line = Line(
            start=Point(min(start_x, end_x), y),
            end=Point(max(start_x, end_x), y),
            color=settings.color,
            layer=settings.layer,
            category=LineCategory.CUT
        )

        if not settings.apply_bridges:
            return [base_line]

        # Create bridge calculator with settings
        calculator = BridgeCalculator(settings.bridge_settings)

        # Apply bridges to the line
        return calculator.apply_bridges(base_line)
