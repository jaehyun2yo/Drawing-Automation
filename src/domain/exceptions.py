"""
Domain layer exceptions for DieCut Automator.

All domain-specific exceptions inherit from DomainException.
"""
from typing import Any


class DomainException(Exception):
    """Base exception for all domain-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(DomainException):
    """Raised when input validation fails."""

    pass


class EntityNotFoundError(DomainException):
    """Raised when a requested entity is not found."""

    pass


class InvalidGeometryError(DomainException):
    """Raised when geometric operations fail due to invalid geometry."""

    pass


class BridgeCalculationError(DomainException):
    """Raised when bridge calculation fails."""

    pass


class FileOperationError(DomainException):
    """Raised when file operations fail."""

    pass


class DxfParseError(FileOperationError):
    """Raised when DXF parsing fails."""

    pass


class DxfWriteError(FileOperationError):
    """Raised when DXF writing fails."""

    pass


class AiParseError(FileOperationError):
    """Raised when AI (Adobe Illustrator) file parsing fails."""

    pass


class FileParseError(FileOperationError):
    """Raised when general file parsing fails."""

    pass


class ConfigurationError(DomainException):
    """Raised when configuration is invalid."""

    pass
