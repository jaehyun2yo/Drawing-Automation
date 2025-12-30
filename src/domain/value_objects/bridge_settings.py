"""
Bridge settings value object.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BridgeSettings:
    """
    Immutable settings for bridge calculation and application.

    Attributes:
        min_length: Minimum line length for bridge application (mm)
        single_bridge_max: Maximum length for single bridge at center (mm)
        target_interval: Target interval between bridges (mm)
        gap_size: Size of the bridge gap/cut (mm)
        edge_margin: Minimum distance from line ends to first bridge (mm)
    """

    min_length: float = 20.0
    single_bridge_max: float = 50.0
    target_interval: float = 60.0
    gap_size: float = 3.0
    edge_margin: float = 10.0

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        if self.min_length <= 0:
            raise ValueError("min_length must be positive")
        if self.single_bridge_max < self.min_length:
            raise ValueError("single_bridge_max must be >= min_length")
        if self.target_interval <= 0:
            raise ValueError("target_interval must be positive")
        if self.gap_size <= 0:
            raise ValueError("gap_size must be positive")
        if self.edge_margin < 0:
            raise ValueError("edge_margin must be non-negative")

    @classmethod
    def default(cls) -> BridgeSettings:
        """Create default bridge settings."""
        return cls()

    @classmethod
    def for_cut(cls) -> BridgeSettings:
        """Create default settings for cut lines."""
        return cls(
            min_length=20.0,
            single_bridge_max=50.0,
            target_interval=60.0,
            gap_size=3.0,
            edge_margin=10.0
        )

    @classmethod
    def for_crease(cls) -> BridgeSettings:
        """Create default settings for crease lines."""
        return cls(
            min_length=20.0,
            single_bridge_max=50.0,
            target_interval=50.0,
            gap_size=2.0,
            edge_margin=10.0
        )
