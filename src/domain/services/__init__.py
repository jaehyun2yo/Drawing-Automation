"""
Domain services for DieCut Automator.
"""
from src.domain.services.bridge_calculator import BridgeCalculator
from src.domain.services.entity_classifier import (
    EntityClassifier,
    UnclassifiedHandling,
    ClassificationResult,
)
from src.domain.services.geometry_service import GeometryService
from src.domain.services.plywood_generator import PlywoodGenerator, PlywoodSettings
from src.domain.services.text_generator import TextGenerator, JobInfo, TextEntity
from src.domain.services.element_remover import ElementRemover, RemovalMode, RemovalResult
from src.domain.services.straight_knife_generator import (
    StraightKnifeGenerator,
    StraightKnifeSettings,
)
from src.domain.services.segment_connector import SegmentConnector, ConnectionResult
from src.domain.services.polyline_bridge_processor import (
    PolylineBridgeProcessor,
    PolylineProcessingResult,
)

__all__ = [
    "BridgeCalculator",
    "EntityClassifier",
    "UnclassifiedHandling",
    "ClassificationResult",
    "GeometryService",
    "PlywoodGenerator",
    "PlywoodSettings",
    "TextGenerator",
    "JobInfo",
    "TextEntity",
    "ElementRemover",
    "RemovalMode",
    "RemovalResult",
    "StraightKnifeGenerator",
    "StraightKnifeSettings",
    "SegmentConnector",
    "ConnectionResult",
    "PolylineBridgeProcessor",
    "PolylineProcessingResult",
]
