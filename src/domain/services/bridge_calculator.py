"""
Bridge Calculator domain service.

Calculates bridge positions and applies bridges to lines.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.domain.value_objects.bridge_settings import BridgeSettings
from src.domain.entities.point import Point
from src.domain.entities.line import Line

if TYPE_CHECKING:
    pass


@dataclass
class BridgeCalculator:
    """
    Service for calculating and applying bridges to lines.

    Bridges are gaps in cutting lines that keep the cut-out piece
    connected to the surrounding material during manufacturing.
    """

    settings: BridgeSettings

    def calculate_bridge_positions(self, line_length: float) -> list[float]:
        """
        Calculate bridge center positions as ratios along the line.

        Args:
            line_length: Length of the line in millimeters

        Returns:
            List of positions as ratios (0.0 to 1.0) where bridges should be placed
        """
        # No bridges for lines shorter than minimum length
        if line_length < self.settings.min_length:
            return []

        # Single bridge at center for lines up to single_bridge_max
        if line_length < self.settings.single_bridge_max:
            return [0.5]

        # Calculate effective length (excluding edge margins)
        effective_length = line_length - (2 * self.settings.edge_margin)

        # If effective length is too small, just put one at center
        if effective_length <= 0:
            return [0.5]

        # Calculate number of bridges based on target interval
        bridge_count = max(1, round(effective_length / self.settings.target_interval))

        # Calculate actual interval
        actual_interval = effective_length / bridge_count

        # Adjust count if interval is out of acceptable range (50-70mm)
        if actual_interval > 70 and bridge_count < effective_length / 50:
            bridge_count += 1
            actual_interval = effective_length / bridge_count
        elif actual_interval < 50 and bridge_count > 1:
            bridge_count -= 1
            actual_interval = effective_length / bridge_count

        # Calculate positions as ratios
        positions: list[float] = []
        for i in range(bridge_count):
            # Position within effective length
            pos_in_effective = (actual_interval / 2) + (actual_interval * i)
            # Convert to absolute position
            absolute_pos = self.settings.edge_margin + pos_in_effective
            # Convert to ratio
            ratio = absolute_pos / line_length
            positions.append(ratio)

        return positions

    def calculate_bridge_gaps(self, line_length: float) -> list[tuple[float, float]]:
        """
        Calculate bridge gap ranges as ratio pairs.

        Args:
            line_length: Length of the line in millimeters

        Returns:
            List of (start_ratio, end_ratio) tuples for each bridge gap
        """
        positions = self.calculate_bridge_positions(line_length)
        if not positions:
            return []

        # Convert gap_size to ratio
        gap_ratio = self.settings.gap_size / line_length

        gaps: list[tuple[float, float]] = []
        for pos in positions:
            start = pos - (gap_ratio / 2)
            end = pos + (gap_ratio / 2)

            # Clamp to valid range
            start = max(0.001, start)
            end = min(0.999, end)

            if start < end:
                gaps.append((start, end))

        return gaps

    def apply_bridges(self, line: Line) -> list[Line]:
        """
        Apply bridges to a line by splitting it into segments.

        Args:
            line: The line to apply bridges to

        Returns:
            List of Line segments with bridges removed
        """
        gaps = self.calculate_bridge_gaps(line.length)

        # No bridges needed
        if not gaps:
            return [line]

        # Create segment split points
        split_ratios: list[float] = []
        for start, end in gaps:
            split_ratios.append(start)
            split_ratios.append(end)

        # Sort and add boundaries
        split_ratios = sorted(set([0.0] + split_ratios + [1.0]))

        # Create segments, skipping gap regions
        segments: list[Line] = []
        for i in range(len(split_ratios) - 1):
            start_ratio = split_ratios[i]
            end_ratio = split_ratios[i + 1]

            # Check if this segment is a gap (should be skipped)
            is_gap = False
            for gap_start, gap_end in gaps:
                # If segment falls within a gap, skip it
                if abs(start_ratio - gap_start) < 0.0001 and abs(end_ratio - gap_end) < 0.0001:
                    is_gap = True
                    break

            if not is_gap:
                start_point = line.point_at_ratio(start_ratio)
                end_point = line.point_at_ratio(end_ratio)

                segment = Line(
                    start=start_point,
                    end=end_point,
                    layer=line.layer,
                    color=line.color,
                    linetype=line.linetype,
                    category=line.category
                )
                segments.append(segment)

        return segments if segments else [line]
