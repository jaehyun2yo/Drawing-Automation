"""Service for processing polylines with bridges."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.entities.polyline import Polyline
from src.domain.entities.entity import Entity
from src.domain.services.bridge_calculator import BridgeCalculator
from src.domain.value_objects.bridge_settings import BridgeSettings
from src.domain.types import LineCategory

if TYPE_CHECKING:
    pass


@dataclass
class PolylineProcessingResult:
    """Result of polyline processing."""

    processed_entities: list[Entity]
    original_polyline_count: int
    decomposed_segment_count: int
    bridged_segment_count: int

    @property
    def total_output_count(self) -> int:
        """Get total number of output entities."""
        return len(self.processed_entities)


@dataclass
class PolylineBridgeProcessor:
    """
    Service for processing polylines with bridge insertion.

    This processor:
    1. Identifies polyline entities in a collection
    2. Decomposes polylines into individual line/arc segments
    3. Applies bridge processing to each segment based on its category
    4. Returns the processed segments along with non-polyline entities
    """

    cut_bridge_settings: BridgeSettings = field(
        default_factory=BridgeSettings.for_cut
    )
    crease_bridge_settings: BridgeSettings = field(
        default_factory=BridgeSettings.for_crease
    )
    process_unknown_as_cut: bool = True

    def process(
        self,
        entities: list[Entity],
        apply_bridges: bool = True
    ) -> PolylineProcessingResult:
        """
        Process all entities, decomposing polylines and applying bridges.

        Args:
            entities: List of entities to process
            apply_bridges: Whether to apply bridges to segments

        Returns:
            PolylineProcessingResult with processed entities
        """
        processed: list[Entity] = []
        original_polyline_count = 0
        decomposed_segment_count = 0
        bridged_segment_count = 0

        for entity in entities:
            if isinstance(entity, Polyline):
                original_polyline_count += 1

                # Decompose polyline into segments
                segments = entity.decompose()
                decomposed_segment_count += len(segments)

                if apply_bridges:
                    # Apply bridges to each segment
                    for segment in segments:
                        bridged = self._apply_bridges_to_segment(segment)
                        processed.extend(bridged)
                        if len(bridged) > 1:
                            bridged_segment_count += 1
                else:
                    processed.extend(segments)
            else:
                # Non-polyline entities pass through unchanged
                processed.append(entity)

        return PolylineProcessingResult(
            processed_entities=processed,
            original_polyline_count=original_polyline_count,
            decomposed_segment_count=decomposed_segment_count,
            bridged_segment_count=bridged_segment_count,
        )

    def decompose_only(self, entities: list[Entity]) -> list[Entity]:
        """
        Decompose polylines without applying bridges.

        Args:
            entities: List of entities to process

        Returns:
            List of entities with polylines decomposed to segments
        """
        result = self.process(entities, apply_bridges=False)
        return result.processed_entities

    def _apply_bridges_to_segment(self, segment: Line | Arc) -> list[Line | Arc]:
        """
        Apply bridges to a single segment.

        Args:
            segment: Line or Arc segment

        Returns:
            List of segments (split by bridges)
        """
        # Only apply bridges to lines for now
        # Arc bridge support could be added later
        if not isinstance(segment, Line):
            return [segment]

        # Determine which bridge settings to use based on category
        category = getattr(segment, 'category', LineCategory.UNKNOWN)

        if category == LineCategory.CUT:
            settings = self.cut_bridge_settings
        elif category == LineCategory.CREASE:
            settings = self.crease_bridge_settings
        elif category == LineCategory.UNKNOWN and self.process_unknown_as_cut:
            settings = self.cut_bridge_settings
        else:
            # No bridges for auxiliary, plywood, or other categories
            return [segment]

        calculator = BridgeCalculator(settings)
        return calculator.apply_bridges(segment)

    def get_polyline_count(self, entities: list[Entity]) -> int:
        """
        Count the number of polyline entities.

        Args:
            entities: List of entities to count

        Returns:
            Number of polyline entities
        """
        return sum(1 for e in entities if isinstance(e, Polyline))

    def get_segment_count(self, entities: list[Entity]) -> int:
        """
        Get total segment count if all polylines were decomposed.

        Args:
            entities: List of entities

        Returns:
            Total number of segments
        """
        count = 0
        for entity in entities:
            if isinstance(entity, Polyline):
                count += entity.segment_count
            else:
                count += 1
        return count
