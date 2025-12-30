"""Application services for DieCut Automator."""
from src.application.services.filename_generator import FilenameGenerator
from src.application.services.preset_manager import Preset, PresetManager
from src.application.services.batch_processor import (
    BatchProcessor,
    BatchProcessorOptions,
    BatchResult,
    BatchItemResult,
    BatchItemStatus,
)

__all__ = [
    "FilenameGenerator",
    "Preset",
    "PresetManager",
    "BatchProcessor",
    "BatchProcessorOptions",
    "BatchResult",
    "BatchItemResult",
    "BatchItemStatus",
]
