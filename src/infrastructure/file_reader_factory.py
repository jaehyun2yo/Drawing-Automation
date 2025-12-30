"""
Factory for creating appropriate file readers based on file extension.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.application.ports.file_reader_port import IFileReader
from src.domain.exceptions import FileParseError

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


class FileReaderFactory:
    """Factory for creating file readers based on file extension."""

    # Mapping of file extensions to reader classes
    _readers: dict[str, type[IFileReader]] = {}

    @classmethod
    def register_reader(cls, extension: str, reader_class: type[IFileReader]) -> None:
        """
        Register a reader class for a file extension.

        Args:
            extension: File extension (e.g., '.dxf', '.ai')
            reader_class: Reader class to use for this extension
        """
        cls._readers[extension.lower()] = reader_class

    @classmethod
    def get_reader(cls, file_path: Path) -> IFileReader:
        """
        Get appropriate reader for a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Appropriate file reader instance

        Raises:
            FileParseError: If no reader is registered for the file extension
        """
        extension = file_path.suffix.lower()

        if extension not in cls._readers:
            supported = ', '.join(cls._readers.keys()) or 'none'
            raise FileParseError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {supported}"
            )

        reader_class = cls._readers[extension]
        return reader_class()

    @classmethod
    def read_file(cls, file_path: Path) -> list[Entity]:
        """
        Convenience method to read a file using the appropriate reader.

        Args:
            file_path: Path to the file

        Returns:
            List of domain entities

        Raises:
            FileParseError: If the file cannot be read
            FileNotFoundError: If the file does not exist
        """
        reader = cls.get_reader(file_path)
        return reader.read(file_path)

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """
        Get list of all supported file extensions.

        Returns:
            List of supported extensions
        """
        return list(cls._readers.keys())

    @classmethod
    def get_file_filter(cls) -> str:
        """
        Get file filter string for file dialogs.

        Returns:
            File filter string (e.g., "Drawing Files (*.dxf *.ai);;All Files (*.*)")
        """
        if not cls._readers:
            return "All Files (*.*)"

        extensions = ' '.join(f'*{ext}' for ext in cls._readers.keys())
        return f"Drawing Files ({extensions});;All Files (*.*)"

    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """
        Check if a file format is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if the file format is supported
        """
        return file_path.suffix.lower() in cls._readers


def _register_default_readers() -> None:
    """Register default file readers."""
    # Import readers here to avoid circular imports
    from src.infrastructure.dxf.ezdxf_adapter import EzdxfReader
    from src.infrastructure.ai.ai_adapter import AiFileReader

    # Register DXF reader
    FileReaderFactory.register_reader('.dxf', EzdxfReader)

    # Register AI/SVG/EPS readers
    FileReaderFactory.register_reader('.ai', AiFileReader)
    FileReaderFactory.register_reader('.svg', AiFileReader)
    FileReaderFactory.register_reader('.eps', AiFileReader)


# Register default readers on module import
_register_default_readers()
