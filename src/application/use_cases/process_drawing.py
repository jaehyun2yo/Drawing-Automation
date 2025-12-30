"""Process drawing use case - main automation pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.domain.types import PlateType, Side, LineCategory
from src.domain.value_objects.bridge_settings import BridgeSettings
from src.domain.value_objects.paper_size import PaperSize
from src.domain.services.bridge_calculator import BridgeCalculator
from src.domain.services.entity_classifier import EntityClassifier
from src.domain.services.geometry_service import GeometryService
from src.domain.services.plywood_generator import PlywoodGenerator, PlywoodSettings
from src.domain.services.text_generator import TextGenerator, JobInfo
from src.domain.services.element_remover import ElementRemover, RemovalMode
from src.domain.services.straight_knife_generator import (
    StraightKnifeGenerator,
    StraightKnifeSettings,
)
from src.domain.services.segment_connector import SegmentConnector
from src.domain.services.polyline_bridge_processor import PolylineBridgeProcessor
from src.domain.entities.line import Line
from src.domain.entities.polyline import Polyline
from src.domain.entities.bounding_box import BoundingBox

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


@dataclass(frozen=True)
class ProcessingOptions:
    """Options for processing a drawing."""

    side: Side = Side.BACK
    plate_type: PlateType = PlateType.COPPER
    apply_bridges: bool = True
    generate_plywood: bool = True
    generate_text: bool = True
    apply_straight_knife: bool = True
    remove_external: bool = True
    connect_segments: bool = False
    decompose_polylines: bool = True  # Decompose polylines for bridge processing
    job_info: JobInfo | None = None
    paper_size: PaperSize | None = None

    # Bridge settings
    cut_bridge_settings: BridgeSettings = field(
        default_factory=BridgeSettings.for_cut
    )
    crease_bridge_settings: BridgeSettings = field(
        default_factory=BridgeSettings.for_crease
    )

    # Segment connection settings
    connection_tolerance: float = 0.1


@dataclass
class ProcessingResult:
    """Result of processing a drawing."""

    entities: list[Entity]
    success: bool = True
    message: str = ""
    statistics: dict | None = None
    removed_count: int = 0
    connection_count: int = 0
    polyline_count: int = 0


@dataclass
class ProcessDrawingUseCase:
    """
    Main use case for processing die-cut drawings.

    This orchestrates the full automation pipeline:
    1. Connect segments (optional)
    2. Decompose polylines into line/arc segments
    3. Classify entities by color/layer
    4. Apply bridges to cut/crease lines
    5. Mirror for front side
    6. Generate plywood frame
    7. Generate straight knives
    8. Generate text entities
    9. Remove external elements
    """

    classifier: EntityClassifier = field(default_factory=EntityClassifier)
    geometry: GeometryService = field(default_factory=GeometryService)
    plywood_gen: PlywoodGenerator = field(default_factory=PlywoodGenerator)
    text_gen: TextGenerator = field(default_factory=TextGenerator)
    element_remover: ElementRemover = field(default_factory=ElementRemover)
    knife_gen: StraightKnifeGenerator = field(default_factory=StraightKnifeGenerator)
    segment_connector: SegmentConnector = field(default_factory=SegmentConnector)
    polyline_processor: PolylineBridgeProcessor = field(
        default_factory=PolylineBridgeProcessor
    )

    def execute(
        self,
        entities: list[Entity],
        options: ProcessingOptions
    ) -> ProcessingResult:
        """
        Execute the drawing processing pipeline.

        Args:
            entities: Input entities from DXF file
            options: Processing options

        Returns:
            ProcessingResult with processed entities
        """
        if not entities:
            return ProcessingResult(
                entities=[],
                success=True,
                message="No entities to process",
                statistics=self._empty_statistics()
            )

        connection_count = 0
        polyline_count = 0

        # Step 1: Connect segments if enabled
        if options.connect_segments:
            self.segment_connector.tolerance = options.connection_tolerance
            result = self.segment_connector.connect_segments(entities)
            entities = result.connected_entities
            connection_count = result.connection_count

        # Step 2: Decompose polylines if enabled
        if options.decompose_polylines:
            polyline_count = self.polyline_processor.get_polyline_count(entities)
            if polyline_count > 0:
                entities = self.polyline_processor.decompose_only(entities)

        # Step 3: Classify entities
        classified = self._classify_entities(entities)

        # Step 4: Apply bridges if enabled
        if options.apply_bridges:
            classified = self._apply_bridges(classified, options)

        # Step 5: Mirror for front side
        if options.side == Side.FRONT:
            classified = self._mirror_entities(classified)

        # Step 6: Generate plywood frame
        result_entities = list(classified)
        plywood_bbox = None
        drawing_bbox = None

        if options.generate_plywood:
            # Get non-plywood entities for bounding box calculation
            drawing_entities = [
                e for e in classified
                if getattr(e, 'category', None) != LineCategory.PLYWOOD
            ]
            if drawing_entities:
                drawing_bbox = self.geometry.calculate_bounding_box(drawing_entities)

                # Use paper size if provided, otherwise calculate from drawing
                if options.paper_size:
                    plywood_settings = PlywoodSettings.for_plate_type(options.plate_type)
                    # Create plywood bbox from paper size
                    plywood_bbox = BoundingBox(
                        min_x=0,
                        min_y=0,
                        max_x=options.paper_size.width,
                        max_y=options.paper_size.height
                    )
                    # Generate plywood rectangle from paper size
                    plywood_lines = self.plywood_gen.generate_rectangle(plywood_bbox)
                    result_entities.extend(plywood_lines)
                else:
                    plywood_settings = PlywoodSettings.for_plate_type(options.plate_type)
                    plywood_lines = self.plywood_gen.generate_for_entities(
                        drawing_entities, plywood_settings
                    )
                    result_entities.extend(plywood_lines)
                    plywood_bbox = self.geometry.calculate_bounding_box(plywood_lines)

        # Step 7: Generate straight knives
        if options.apply_straight_knife and plywood_bbox and drawing_bbox:
            knife_settings = StraightKnifeSettings(
                apply_bridges=options.apply_bridges,
                bridge_settings=options.cut_bridge_settings
            )
            knife_lines = self.knife_gen.generate_at_center(
                drawing_bbox, plywood_bbox, knife_settings
            )
            result_entities.extend(knife_lines)

        # Step 8: Generate text entities
        if options.generate_text and options.job_info and plywood_bbox:
            texts = self.text_gen.generate_positioned_texts(
                options.job_info, plywood_bbox
            )
            result_entities.extend(texts)

        # Step 9: Remove external elements
        removed_count = 0
        if options.remove_external and plywood_bbox:
            removal_result = self.element_remover.remove_external_elements(
                result_entities, plywood_bbox, RemovalMode.REMOVE_ALL
            )
            result_entities = removal_result.kept_entities
            removed_count = removal_result.removal_count

        # Calculate statistics
        statistics = self._calculate_statistics(result_entities)

        return ProcessingResult(
            entities=result_entities,
            success=True,
            message="Processing completed successfully",
            statistics=statistics,
            removed_count=removed_count,
            connection_count=connection_count,
            polyline_count=polyline_count
        )

    def _classify_entities(self, entities: list[Entity]) -> list[Entity]:
        """Classify all entities by color and layer."""
        return self.classifier.apply_categories(entities)

    def _apply_bridges(
        self,
        entities: list[Entity],
        options: ProcessingOptions
    ) -> list[Entity]:
        """Apply bridges to cut and crease lines."""
        result = []

        cut_calculator = BridgeCalculator(options.cut_bridge_settings)
        crease_calculator = BridgeCalculator(options.crease_bridge_settings)

        for entity in entities:
            if not isinstance(entity, Line):
                result.append(entity)
                continue

            category = getattr(entity, 'category', None)
            if category == LineCategory.CUT:
                segments = cut_calculator.apply_bridges(entity)
                result.extend(segments)
            elif category == LineCategory.CREASE:
                segments = crease_calculator.apply_bridges(entity)
                result.extend(segments)
            else:
                result.append(entity)

        return result

    def _mirror_entities(self, entities: list[Entity]) -> list[Entity]:
        """Mirror entities for front side processing."""
        # Calculate center X for mirroring
        bbox = self.geometry.calculate_bounding_box(entities)
        if bbox is None:
            return entities

        center_x = bbox.center.x
        return self.geometry.mirror_entities_x(entities, center_x)

    def _calculate_statistics(self, entities: list[Entity]) -> dict:
        """Calculate processing statistics."""
        from src.domain.services.text_generator import TextEntity

        stats = {
            'total_count': len(entities),
            'cut_count': 0,
            'crease_count': 0,
            'auxiliary_count': 0,
            'plywood_count': 0,
            'text_count': 0,
            'unknown_count': 0,
        }

        for entity in entities:
            if isinstance(entity, TextEntity):
                stats['text_count'] += 1
                continue

            category = getattr(entity, 'category', LineCategory.UNKNOWN)
            if category == LineCategory.CUT:
                stats['cut_count'] += 1
            elif category == LineCategory.CREASE:
                stats['crease_count'] += 1
            elif category == LineCategory.AUXILIARY:
                stats['auxiliary_count'] += 1
            elif category == LineCategory.PLYWOOD:
                stats['plywood_count'] += 1
            else:
                stats['unknown_count'] += 1

        return stats

    def _empty_statistics(self) -> dict:
        """Return empty statistics dict."""
        return {
            'total_count': 0,
            'cut_count': 0,
            'crease_count': 0,
            'auxiliary_count': 0,
            'plywood_count': 0,
            'text_count': 0,
            'unknown_count': 0,
        }
