"""Geometry service for spatial operations on entities."""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, TypeVar

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.entities.bounding_box import BoundingBox

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity

T = TypeVar('T', bound='Entity')


@dataclass
class GeometryService:
    """Service for geometric operations on entities."""

    def calculate_bounding_box(
        self, entities: list[Entity]
    ) -> BoundingBox | None:
        """
        Calculate the bounding box that contains all entities.

        Args:
            entities: List of entities

        Returns:
            BoundingBox containing all entities, or None if empty
        """
        if not entities:
            return None

        boxes = [entity.bounding_box for entity in entities]
        result = boxes[0]

        for box in boxes[1:]:
            result = result.union(box)

        return result

    def mirror_x(self, entity: T, center_x: float) -> T:
        """
        Mirror an entity across a vertical line at center_x.

        Args:
            entity: Entity to mirror
            center_x: X coordinate of the mirror axis

        Returns:
            New mirrored entity
        """
        if isinstance(entity, Line):
            return self._mirror_line_x(entity, center_x)
        elif isinstance(entity, Arc):
            return self._mirror_arc_x(entity, center_x)
        else:
            # Try using the entity's mirror_x method if available
            if hasattr(entity, 'mirror_x'):
                return entity.mirror_x(center_x)
            raise NotImplementedError(f"Cannot mirror {type(entity)}")

    def _mirror_line_x(self, line: Line, center_x: float) -> Line:
        """Mirror a line across vertical axis."""
        new_start = line.start.mirror_x(center_x)
        new_end = line.end.mirror_x(center_x)
        return replace(line, start=new_start, end=new_end)

    def _mirror_arc_x(self, arc: Arc, center_x: float) -> Arc:
        """Mirror an arc across vertical axis."""
        new_center = arc.center.mirror_x(center_x)
        # Mirror angles: when mirroring across X axis, angles are reflected
        new_start_angle = 180 - arc.end_angle
        new_end_angle = 180 - arc.start_angle
        return replace(
            arc,
            center=new_center,
            start_angle=new_start_angle,
            end_angle=new_end_angle
        )

    def mirror_entities_x(
        self, entities: list[Entity], center_x: float
    ) -> list[Entity]:
        """
        Mirror all entities across a vertical line.

        Args:
            entities: List of entities to mirror
            center_x: X coordinate of the mirror axis

        Returns:
            List of mirrored entities
        """
        return [self.mirror_x(entity, center_x) for entity in entities]

    def translate(self, entity: T, dx: float, dy: float) -> T:
        """
        Translate an entity by offset.

        Args:
            entity: Entity to translate
            dx: X offset
            dy: Y offset

        Returns:
            New translated entity
        """
        if isinstance(entity, Line):
            return self._translate_line(entity, dx, dy)
        elif isinstance(entity, Arc):
            return self._translate_arc(entity, dx, dy)
        else:
            if hasattr(entity, 'translate'):
                return entity.translate(dx, dy)
            raise NotImplementedError(f"Cannot translate {type(entity)}")

    def _translate_line(self, line: Line, dx: float, dy: float) -> Line:
        """Translate a line by offset."""
        new_start = line.start.translate(dx, dy)
        new_end = line.end.translate(dx, dy)
        return replace(line, start=new_start, end=new_end)

    def _translate_arc(self, arc: Arc, dx: float, dy: float) -> Arc:
        """Translate an arc by offset."""
        new_center = arc.center.translate(dx, dy)
        return replace(arc, center=new_center)

    def translate_entities(
        self, entities: list[Entity], dx: float, dy: float
    ) -> list[Entity]:
        """
        Translate all entities by offset.

        Args:
            entities: List of entities to translate
            dx: X offset
            dy: Y offset

        Returns:
            List of translated entities
        """
        return [self.translate(entity, dx, dy) for entity in entities]

    def center_at(
        self, entities: list[Entity], target: Point
    ) -> list[Entity]:
        """
        Move entities so their center is at the target point.

        Args:
            entities: List of entities
            target: Target center point

        Returns:
            List of centered entities
        """
        bbox = self.calculate_bounding_box(entities)
        if bbox is None:
            return entities

        current_center = bbox.center
        dx = target.x - current_center.x
        dy = target.y - current_center.y

        return self.translate_entities(entities, dx, dy)

    def distance(self, p1: Point, p2: Point) -> float:
        """
        Calculate Euclidean distance between two points.

        Args:
            p1: First point
            p2: Second point

        Returns:
            Distance between points
        """
        return p1.distance_to(p2)
