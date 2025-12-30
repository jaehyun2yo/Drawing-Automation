"""Service for removing elements outside plywood area."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

from src.domain.entities.bounding_box import BoundingBox
from src.domain.types import LineCategory

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


class RemovalMode(Enum):
    """Mode for handling elements outside plywood."""

    REMOVE_ALL = auto()        # Remove all external elements
    KEEP_AUXILIARY = auto()    # Keep auxiliary lines
    KEEP_TEXT = auto()         # Keep text elements
    CONFIRM_EACH = auto()      # Mark for confirmation (not auto-remove)


@dataclass(frozen=True, slots=True)
class RemovalResult:
    """Result of element removal operation."""

    kept_entities: list
    removed_entities: list
    removal_count: int

    @property
    def kept_count(self) -> int:
        """Number of entities kept."""
        return len(self.kept_entities)


@dataclass
class ElementRemover:
    """
    Service for identifying and removing elements outside plywood area.

    Removes entities that are completely outside the plywood bounding box,
    while preserving entities that are inside or intersecting the boundary.
    """

    # Layers to exclude from removal (always keep)
    exclude_layers: list[str] = field(default_factory=lambda: ["PLYWOOD", "TEXT"])

    # Categories to always keep
    keep_categories: list[LineCategory] = field(
        default_factory=lambda: [LineCategory.PLYWOOD]
    )

    def identify_external_elements(
        self,
        entities: list[Entity],
        plywood_bbox: BoundingBox
    ) -> list[Entity]:
        """
        Identify entities that are completely outside the plywood area.

        Args:
            entities: List of entities to check
            plywood_bbox: Bounding box of the plywood frame

        Returns:
            List of entities that are completely outside
        """
        external = []

        for entity in entities:
            # Skip if in excluded layer
            layer = getattr(entity, 'layer', None)
            if layer and layer.upper() in [l.upper() for l in self.exclude_layers]:
                continue

            # Skip if category should be kept
            category = getattr(entity, 'category', None)
            if category in self.keep_categories:
                continue

            # Check if entity is completely outside
            if self._is_completely_outside(entity, plywood_bbox):
                external.append(entity)

        return external

    def remove_external_elements(
        self,
        entities: list[Entity],
        plywood_bbox: BoundingBox,
        mode: RemovalMode = RemovalMode.REMOVE_ALL
    ) -> RemovalResult:
        """
        Remove elements outside plywood area based on mode.

        Args:
            entities: List of all entities
            plywood_bbox: Bounding box of the plywood frame
            mode: Removal mode determining which elements to remove

        Returns:
            RemovalResult with kept and removed entities
        """
        from src.domain.services.text_generator import TextEntity

        kept = []
        removed = []

        for entity in entities:
            should_remove = False

            # Check if completely outside
            if self._is_completely_outside(entity, plywood_bbox):
                # Check exceptions based on mode
                layer = getattr(entity, 'layer', None)
                category = getattr(entity, 'category', None)

                # Always keep plywood
                if category == LineCategory.PLYWOOD:
                    should_remove = False
                # Always keep entities in excluded layers
                elif layer and layer.upper() in [l.upper() for l in self.exclude_layers]:
                    should_remove = False
                # Mode-specific handling
                elif mode == RemovalMode.REMOVE_ALL:
                    should_remove = True
                elif mode == RemovalMode.KEEP_AUXILIARY:
                    should_remove = category != LineCategory.AUXILIARY
                elif mode == RemovalMode.KEEP_TEXT:
                    should_remove = not isinstance(entity, TextEntity)
                elif mode == RemovalMode.CONFIRM_EACH:
                    # Mark but don't remove - handled by UI
                    should_remove = False

            if should_remove:
                removed.append(entity)
            else:
                kept.append(entity)

        return RemovalResult(
            kept_entities=kept,
            removed_entities=removed,
            removal_count=len(removed)
        )

    def _is_completely_outside(
        self,
        entity: Entity,
        plywood_bbox: BoundingBox
    ) -> bool:
        """
        Check if an entity is completely outside the plywood area.

        Args:
            entity: Entity to check
            plywood_bbox: Plywood bounding box

        Returns:
            True if entity is completely outside
        """
        from src.domain.entities.line import Line
        from src.domain.entities.arc import Arc
        from src.domain.services.text_generator import TextEntity

        # Get entity bounding box
        entity_bbox = self._get_entity_bbox(entity)

        if entity_bbox is None:
            # If we can't determine bbox, keep it
            return False

        # Check if completely outside
        # Entity is outside if any of these conditions is true:
        # - Entity's max_x < plywood's min_x (entirely to the left)
        # - Entity's min_x > plywood's max_x (entirely to the right)
        # - Entity's max_y < plywood's min_y (entirely below)
        # - Entity's min_y > plywood's max_y (entirely above)
        return (
            entity_bbox.max_x < plywood_bbox.min_x or
            entity_bbox.min_x > plywood_bbox.max_x or
            entity_bbox.max_y < plywood_bbox.min_y or
            entity_bbox.min_y > plywood_bbox.max_y
        )

    def _get_entity_bbox(self, entity: Entity) -> BoundingBox | None:
        """Get bounding box of an entity."""
        from src.domain.entities.line import Line
        from src.domain.entities.arc import Arc
        from src.domain.services.text_generator import TextEntity

        if isinstance(entity, Line):
            return BoundingBox(
                min_x=min(entity.start.x, entity.end.x),
                min_y=min(entity.start.y, entity.end.y),
                max_x=max(entity.start.x, entity.end.x),
                max_y=max(entity.start.y, entity.end.y)
            )
        elif isinstance(entity, Arc):
            # Approximate arc bbox (not exact but sufficient for removal check)
            return BoundingBox(
                min_x=entity.center.x - entity.radius,
                min_y=entity.center.y - entity.radius,
                max_x=entity.center.x + entity.radius,
                max_y=entity.center.y + entity.radius
            )
        elif isinstance(entity, TextEntity):
            # Text bbox (approximate based on position)
            return BoundingBox(
                min_x=entity.position.x,
                min_y=entity.position.y,
                max_x=entity.position.x + len(entity.content) * entity.height * 0.6,
                max_y=entity.position.y + entity.height
            )

        return None
