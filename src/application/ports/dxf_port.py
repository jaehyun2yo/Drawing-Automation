"""
Port interfaces for DXF file operations.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


class IDxfReader(ABC):
    """Interface for reading DXF files."""

    @abstractmethod
    def read(self, file_path: Path) -> list[Entity]:
        """
        Read entities from a DXF file.

        Args:
            file_path: Path to the DXF file

        Returns:
            List of domain entities parsed from the file

        Raises:
            DxfParseError: If the file cannot be parsed
            FileNotFoundError: If the file does not exist
        """
        ...

    @abstractmethod
    def get_file_info(self, file_path: Path) -> dict[str, any]:
        """
        Get metadata about a DXF file without fully parsing it.

        Args:
            file_path: Path to the DXF file

        Returns:
            Dictionary with file info (version, entity count, etc.)
        """
        ...


class IDxfWriter(ABC):
    """Interface for writing DXF files."""

    @abstractmethod
    def write(
        self,
        entities: list[Entity],
        file_path: Path,
        version: str = "AC1024"
    ) -> None:
        """
        Write entities to a DXF file.

        Args:
            entities: List of domain entities to write
            file_path: Path to save the DXF file
            version: DXF version string (default: AC1024 = AutoCAD 2010)

        Raises:
            DxfWriteError: If the file cannot be written
        """
        ...
