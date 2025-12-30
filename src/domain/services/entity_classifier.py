"""Entity classifier service for categorizing DXF entities."""
from __future__ import annotations

from dataclasses import dataclass, replace, field
from enum import Enum, auto
from typing import TYPE_CHECKING

from src.domain.types import LineCategory, StandardColor

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


class UnclassifiedHandling(Enum):
    """Options for handling unclassified entities."""

    TREAT_AS_CUT = auto()      # Treat unclassified as CUT lines
    TREAT_AS_CREASE = auto()   # Treat unclassified as CREASE lines
    TREAT_AS_AUXILIARY = auto() # Treat unclassified as AUXILIARY lines
    KEEP_UNKNOWN = auto()       # Keep as UNKNOWN (no special handling)
    SKIP = auto()               # Skip/exclude from output


@dataclass
class ClassificationResult:
    """Result of entity classification with statistics."""

    classified_entities: list["Entity"]
    unclassified_count: int
    statistics: dict[LineCategory, int]

    @property
    def total_count(self) -> int:
        """Get total entity count."""
        return len(self.classified_entities) + self.unclassified_count


@dataclass
class EntityClassifier:
    """Service for classifying entities by layer name and color."""

    # Layer name patterns for each category (case-insensitive)
    LAYER_PATTERNS: dict[LineCategory, list[str]] = None

    # Color mappings
    COLOR_MAP: dict[int, LineCategory] = None

    # How to handle unclassified entities
    unclassified_handling: UnclassifiedHandling = UnclassifiedHandling.TREAT_AS_CUT

    def __post_init__(self) -> None:
        """Initialize default patterns and mappings."""
        if self.LAYER_PATTERNS is None:
            self.LAYER_PATTERNS = {
                LineCategory.CUT: ["CUT", "칼", "KNIFE", "DIE"],
                LineCategory.CREASE: ["CREASE", "괘", "FOLD", "SCORE"],
                LineCategory.AUXILIARY: ["AUX", "HELPER", "보조"],
                LineCategory.PLYWOOD: ["PLYWOOD", "합판", "FRAME", "WOOD"],
            }

        if self.COLOR_MAP is None:
            self.COLOR_MAP = {
                StandardColor.RED: LineCategory.CUT,
                StandardColor.BLUE: LineCategory.CREASE,
                StandardColor.GREEN: LineCategory.AUXILIARY,
                StandardColor.WHITE: LineCategory.PLYWOOD,
            }

    def classify(self, entity: Entity) -> LineCategory:
        """
        Classify an entity by its layer name and color.

        Layer name takes precedence over color.

        Args:
            entity: Entity to classify

        Returns:
            LineCategory for the entity
        """
        # First try to classify by layer name
        layer = getattr(entity, 'layer', '0')
        if layer and layer not in ('0', ''):
            category = self._classify_by_layer(layer)
            if category != LineCategory.UNKNOWN:
                return category

        # Fall back to color classification
        color = getattr(entity, 'color', None)
        if color is not None:
            category = self._classify_by_color(color)
            if category != LineCategory.UNKNOWN:
                return category

        return LineCategory.UNKNOWN

    def _classify_by_layer(self, layer_name: str) -> LineCategory:
        """
        Classify by layer name.

        Args:
            layer_name: Name of the layer

        Returns:
            LineCategory or UNKNOWN if no match
        """
        layer_upper = layer_name.upper()

        for category, patterns in self.LAYER_PATTERNS.items():
            for pattern in patterns:
                if pattern.upper() in layer_upper:
                    return category

        return LineCategory.UNKNOWN

    def _classify_by_color(self, color: int) -> LineCategory:
        """
        Classify by ACI color.

        Args:
            color: AutoCAD Color Index value

        Returns:
            LineCategory or UNKNOWN if no match
        """
        return self.COLOR_MAP.get(color, LineCategory.UNKNOWN)

    def classify_all(
        self, entities: list[Entity]
    ) -> dict[LineCategory, list[Entity]]:
        """
        Classify all entities and group by category.

        Args:
            entities: List of entities to classify

        Returns:
            Dictionary mapping categories to lists of entities
        """
        result: dict[LineCategory, list[Entity]] = {
            category: [] for category in LineCategory
        }

        for entity in entities:
            category = self.classify(entity)
            result[category].append(entity)

        return result

    def apply_category(self, entity: Entity) -> Entity:
        """
        Apply the classified category to an entity.

        Args:
            entity: Entity to update

        Returns:
            New entity with category set
        """
        category = self.classify(entity)
        return replace(entity, category=category)

    def apply_categories(self, entities: list[Entity]) -> list[Entity]:
        """
        Apply categories to all entities.

        Args:
            entities: List of entities

        Returns:
            List of entities with categories applied
        """
        return [self.apply_category(entity) for entity in entities]

    def apply_categories_with_result(
        self, entities: list[Entity]
    ) -> ClassificationResult:
        """
        Apply categories to all entities with detailed result.

        Handles unclassified entities according to unclassified_handling setting.

        Args:
            entities: List of entities

        Returns:
            ClassificationResult with entities and statistics
        """
        result_entities: list[Entity] = []
        statistics: dict[LineCategory, int] = {cat: 0 for cat in LineCategory}
        unclassified_count = 0

        for entity in entities:
            category = self.classify(entity)

            if category == LineCategory.UNKNOWN:
                unclassified_count += 1

                # Apply unclassified handling policy
                if self.unclassified_handling == UnclassifiedHandling.SKIP:
                    continue
                elif self.unclassified_handling == UnclassifiedHandling.TREAT_AS_CUT:
                    category = LineCategory.CUT
                elif self.unclassified_handling == UnclassifiedHandling.TREAT_AS_CREASE:
                    category = LineCategory.CREASE
                elif self.unclassified_handling == UnclassifiedHandling.TREAT_AS_AUXILIARY:
                    category = LineCategory.AUXILIARY
                # KEEP_UNKNOWN: category stays as UNKNOWN

            updated_entity = replace(entity, category=category)
            result_entities.append(updated_entity)
            statistics[category] += 1

        return ClassificationResult(
            classified_entities=result_entities,
            unclassified_count=unclassified_count,
            statistics=statistics,
        )

    def count_unclassified(self, entities: list[Entity]) -> int:
        """
        Count unclassified entities without modifying them.

        Args:
            entities: List of entities

        Returns:
            Number of entities that would be UNKNOWN
        """
        return sum(
            1 for entity in entities
            if self.classify(entity) == LineCategory.UNKNOWN
        )

    def get_unclassified_entities(self, entities: list[Entity]) -> list[Entity]:
        """
        Get list of entities that cannot be classified.

        Args:
            entities: List of entities

        Returns:
            List of unclassified entities
        """
        return [
            entity for entity in entities
            if self.classify(entity) == LineCategory.UNKNOWN
        ]
