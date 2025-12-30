"""Paper size value object."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class PaperSize:
    """
    Value object representing paper size.

    Attributes:
        name: Display name of the paper size
        width: Width in millimeters
        height: Height in millimeters
    """

    name: str
    width: float
    height: float

    # Standard paper sizes (Korean and ISO)
    STANDARD_SIZES: ClassVar[dict[str, tuple[float, float]]] = {
        "국전": (636, 939),
        "국반절": (636, 469),
        "국4절": (318, 469),
        "4x6전지": (788, 1091),
        "4x6반절": (545, 788),
        "4x6 4절": (394, 545),
        "46판": (394, 545),
        "A1": (594, 841),
        "A2": (420, 594),
        "A3": (297, 420),
        "A4": (210, 297),
    }

    # Size constraints
    MIN_SIZE: ClassVar[float] = 100.0
    MAX_WIDTH: ClassVar[float] = 2000.0
    MAX_HEIGHT: ClassVar[float] = 3000.0

    def __post_init__(self) -> None:
        """Validate paper size dimensions."""
        if self.width < self.MIN_SIZE:
            raise ValueError(f"Width must be at least {self.MIN_SIZE}mm")
        if self.height < self.MIN_SIZE:
            raise ValueError(f"Height must be at least {self.MIN_SIZE}mm")
        if self.width > self.MAX_WIDTH:
            raise ValueError(f"Width must not exceed {self.MAX_WIDTH}mm")
        if self.height > self.MAX_HEIGHT:
            raise ValueError(f"Height must not exceed {self.MAX_HEIGHT}mm")

    @classmethod
    def from_standard(cls, name: str) -> PaperSize:
        """
        Create a PaperSize from a standard size name.

        Args:
            name: Standard size name (e.g., "국전", "A3")

        Returns:
            PaperSize for the standard size

        Raises:
            ValueError: If name is not a known standard size
        """
        if name not in cls.STANDARD_SIZES:
            raise ValueError(f"Unknown standard size: {name}")
        width, height = cls.STANDARD_SIZES[name]
        return cls(name=name, width=width, height=height)

    @classmethod
    def custom(cls, width: float, height: float) -> PaperSize:
        """
        Create a custom PaperSize.

        Args:
            width: Width in millimeters
            height: Height in millimeters

        Returns:
            Custom PaperSize instance
        """
        name = f"{width:.0f}x{height:.0f}"
        return cls(name=name, width=width, height=height)

    @classmethod
    def get_standard_names(cls) -> list[str]:
        """Get list of all standard paper size names."""
        return list(cls.STANDARD_SIZES.keys())

    @property
    def area(self) -> float:
        """Calculate paper area in square millimeters."""
        return self.width * self.height

    @property
    def is_landscape(self) -> bool:
        """Check if paper is in landscape orientation."""
        return self.width > self.height

    @property
    def is_portrait(self) -> bool:
        """Check if paper is in portrait orientation."""
        return self.height > self.width

    def rotate(self) -> PaperSize:
        """Return rotated paper size (swap width and height)."""
        return PaperSize(
            name=f"{self.name} (회전)",
            width=self.height,
            height=self.width
        )

    def fits_drawing(self, drawing_width: float, drawing_height: float) -> bool:
        """
        Check if a drawing fits within this paper size.

        Args:
            drawing_width: Drawing width
            drawing_height: Drawing height

        Returns:
            True if drawing fits within paper
        """
        return drawing_width <= self.width and drawing_height <= self.height
