"""
Common type definitions for DieCut Automator domain layer.
"""
from enum import Enum, auto
from typing import TypeAlias


# Coordinate types
Coordinate: TypeAlias = float
Coordinates2D: TypeAlias = tuple[Coordinate, Coordinate]


class EntityType(Enum):
    """Types of DXF entities supported by the system."""

    LINE = auto()
    ARC = auto()
    CIRCLE = auto()
    POLYLINE = auto()
    LWPOLYLINE = auto()
    SPLINE = auto()
    ELLIPSE = auto()
    TEXT = auto()
    MTEXT = auto()


class LineCategory(Enum):
    """Category of line for processing."""

    CUT = auto()       # Cutting line (knife)
    CREASE = auto()    # Creasing/folding line
    AUXILIARY = auto() # Auxiliary/helper line
    PLYWOOD = auto()   # Plywood frame line
    UNKNOWN = auto()   # Unclassified


class PlateType(Enum):
    """Type of plate for processing."""

    COPPER = auto()  # Copper plate (bottom margin 25mm)
    AUTO = auto()    # Auto plate (bottom margin 15mm)


class Side(Enum):
    """Side of the drawing (front or back)."""

    FRONT = auto()  # Front side (requires mirroring)
    BACK = auto()   # Back side (no mirroring)


class ProcessingStatus(Enum):
    """Status of processing operation."""

    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    ERROR = auto()


# AutoCAD Color Index (ACI) type
ACIColor: TypeAlias = int

# RGB Color type
RGBColor: TypeAlias = tuple[int, int, int]


class StandardColor:
    """Standard AutoCAD Color Index values."""

    RED = 1       # Cut line
    YELLOW = 2
    GREEN = 3     # Auxiliary line
    CYAN = 4
    BLUE = 5      # Crease line
    MAGENTA = 6
    WHITE = 7     # Plywood, text (displays as black on white background)
    BYLAYER = 256  # Color inherited from layer
    BYBLOCK = 0    # Color inherited from block
