"""
Port interfaces for file reading operations.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


class IFileReader(ABC):
    """Interface for reading drawing files (DXF, AI, etc.)."""

    @abstractmethod
    def read(self, file_path: Path) -> list[Entity]:
        """
        Read entities from a drawing file.

        Args:
            file_path: Path to the drawing file

        Returns:
            List of domain entities parsed from the file

        Raises:
            FileParseError: If the file cannot be parsed
            FileNotFoundError: If the file does not exist
        """
        ...

    @abstractmethod
    def get_file_info(self, file_path: Path) -> dict[str, Any]:
        """
        Get metadata about a drawing file without fully parsing it.

        Args:
            file_path: Path to the drawing file

        Returns:
            Dictionary with file info (format, entity count, etc.)
        """
        ...

    @classmethod
    @abstractmethod
    def supported_extensions(cls) -> list[str]:
        """
        Get list of supported file extensions.

        Returns:
            List of supported extensions (e.g., ['.dxf', '.ai'])
        """
        ...
