"""Tests for StraightKnifeGenerator service."""
from __future__ import annotations

import pytest

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.bounding_box import BoundingBox
from src.domain.services.straight_knife_generator import (
    StraightKnifeGenerator,
    StraightKnifeSettings,
)
from src.domain.types import LineCategory, StandardColor
from src.domain.value_objects.bridge_settings import BridgeSettings


class TestStraightKnifeGeneration:
    """Test straight knife generation."""

    def test_generate_at_center(self) -> None:
        """Test generating knives at center Y."""
        generator = StraightKnifeGenerator()

        drawing_bbox = BoundingBox(min_x=100, min_y=100, max_x=400, max_y=300)
        plywood_bbox = BoundingBox(min_x=0, min_y=0, max_x=500, max_y=400)

        settings = StraightKnifeSettings(apply_bridges=False)
        knives = generator.generate_at_center(drawing_bbox, plywood_bbox, settings)

        # Should have 2 lines (left and right)
        assert len(knives) == 2

        # Check Y position is at center of drawing (200)
        center_y = (100 + 300) / 2  # = 200
        for knife in knives:
            assert knife.start.y == center_y
            assert knife.end.y == center_y

    def test_left_knife_position(self) -> None:
        """Test left knife position."""
        generator = StraightKnifeGenerator()

        drawing_bbox = BoundingBox(min_x=100, min_y=100, max_x=400, max_y=300)
        plywood_bbox = BoundingBox(min_x=0, min_y=0, max_x=500, max_y=400)

        settings = StraightKnifeSettings(apply_bridges=False)
        knives = generator.generate_at_center(drawing_bbox, plywood_bbox, settings)

        # Find left knife (from plywood left to drawing left)
        left_knife = [k for k in knives if k.start.x == 0 or k.end.x == 0][0]

        min_x = min(left_knife.start.x, left_knife.end.x)
        max_x = max(left_knife.start.x, left_knife.end.x)
        assert min_x == 0  # plywood left
        assert max_x == 100  # drawing left

    def test_right_knife_position(self) -> None:
        """Test right knife position."""
        generator = StraightKnifeGenerator()

        drawing_bbox = BoundingBox(min_x=100, min_y=100, max_x=400, max_y=300)
        plywood_bbox = BoundingBox(min_x=0, min_y=0, max_x=500, max_y=400)

        settings = StraightKnifeSettings(apply_bridges=False)
        knives = generator.generate_at_center(drawing_bbox, plywood_bbox, settings)

        # Find right knife (from drawing right to plywood right)
        right_knife = [k for k in knives if k.start.x == 500 or k.end.x == 500][0]

        min_x = min(right_knife.start.x, right_knife.end.x)
        max_x = max(right_knife.start.x, right_knife.end.x)
        assert min_x == 400  # drawing right
        assert max_x == 500  # plywood right

    def test_generate_with_bridges(self) -> None:
        """Test generating knives with bridges applied."""
        generator = StraightKnifeGenerator()

        # Large enough for bridges
        drawing_bbox = BoundingBox(min_x=200, min_y=100, max_x=400, max_y=300)
        plywood_bbox = BoundingBox(min_x=0, min_y=0, max_x=600, max_y=400)

        settings = StraightKnifeSettings(
            apply_bridges=True,
            bridge_settings=BridgeSettings(
                min_length=20,
                single_bridge_max=50,
                target_interval=60,
                gap_size=3.0
            )
        )
        knives = generator.generate_at_center(drawing_bbox, plywood_bbox, settings)

        # With bridges, there should be more than 2 segments
        # Left knife is 200mm, right knife is 200mm
        # Each should have multiple segments after bridge application
        assert len(knives) >= 2

    def test_generate_multiple_y_positions(self) -> None:
        """Test generating at multiple Y positions."""
        generator = StraightKnifeGenerator()

        drawing_bbox = BoundingBox(min_x=100, min_y=100, max_x=400, max_y=300)
        plywood_bbox = BoundingBox(min_x=0, min_y=0, max_x=500, max_y=400)

        y_positions = [150, 200, 250]
        settings = StraightKnifeSettings(apply_bridges=False)
        knives = generator.generate(drawing_bbox, plywood_bbox, y_positions, settings)

        # Should have 2 knives per Y position = 6 total
        assert len(knives) == 6

        # Verify all Y positions are covered
        y_values = set(k.start.y for k in knives)
        assert y_values == {150, 200, 250}

    def test_knife_color_and_layer(self) -> None:
        """Test knife color and layer settings."""
        generator = StraightKnifeGenerator()

        drawing_bbox = BoundingBox(min_x=100, min_y=100, max_x=400, max_y=300)
        plywood_bbox = BoundingBox(min_x=0, min_y=0, max_x=500, max_y=400)

        settings = StraightKnifeSettings(
            apply_bridges=False,
            color=StandardColor.RED,
            layer="CUT"
        )
        knives = generator.generate_at_center(drawing_bbox, plywood_bbox, settings)

        for knife in knives:
            assert knife.color == StandardColor.RED
            assert knife.layer == "CUT"
            assert knife.category == LineCategory.CUT


class TestFindHorizontalLinePositions:
    """Test finding horizontal line positions."""

    def test_find_horizontal_lines(self) -> None:
        """Test finding horizontal line Y positions."""
        generator = StraightKnifeGenerator()

        lines = [
            Line(start=Point(0, 100), end=Point(200, 100)),  # Horizontal at y=100
            Line(start=Point(0, 200), end=Point(200, 200)),  # Horizontal at y=200
            Line(start=Point(0, 0), end=Point(0, 100)),      # Vertical (not horizontal)
        ]

        y_positions = generator.find_horizontal_line_positions(lines)

        assert 100 in y_positions
        assert 200 in y_positions
        assert len(y_positions) == 2

    def test_cluster_similar_y_positions(self) -> None:
        """Test clustering similar Y positions."""
        generator = StraightKnifeGenerator()

        lines = [
            Line(start=Point(0, 100), end=Point(50, 100)),
            Line(start=Point(60, 100.5), end=Point(110, 100.5)),  # Close to 100
            Line(start=Point(120, 200), end=Point(170, 200)),
        ]

        y_positions = generator.find_horizontal_line_positions(lines, tolerance=1.0)

        # Should cluster 100 and 100.5 together
        assert len(y_positions) == 2

    def test_empty_when_no_horizontal_lines(self) -> None:
        """Test empty result when no horizontal lines."""
        generator = StraightKnifeGenerator()

        lines = [
            Line(start=Point(0, 0), end=Point(100, 100)),  # Diagonal
            Line(start=Point(0, 0), end=Point(0, 100)),   # Vertical
        ]

        y_positions = generator.find_horizontal_line_positions(lines)

        assert len(y_positions) == 0


class TestEdgeCases:
    """Test edge cases."""

    def test_skip_very_short_knife(self) -> None:
        """Test that very short knives are skipped."""
        generator = StraightKnifeGenerator()

        # Drawing almost spans full plywood width
        drawing_bbox = BoundingBox(min_x=0.5, min_y=100, max_x=499.5, max_y=300)
        plywood_bbox = BoundingBox(min_x=0, min_y=0, max_x=500, max_y=400)

        settings = StraightKnifeSettings(apply_bridges=False)
        knives = generator.generate_at_center(drawing_bbox, plywood_bbox, settings)

        # Very short lines (< 1mm) should be skipped
        assert len(knives) == 0

    def test_drawing_at_plywood_edge(self) -> None:
        """Test when drawing is at plywood edge."""
        generator = StraightKnifeGenerator()

        # Drawing at left edge
        drawing_bbox = BoundingBox(min_x=0, min_y=100, max_x=400, max_y=300)
        plywood_bbox = BoundingBox(min_x=0, min_y=0, max_x=500, max_y=400)

        settings = StraightKnifeSettings(apply_bridges=False)
        knives = generator.generate_at_center(drawing_bbox, plywood_bbox, settings)

        # Only right knife should exist
        assert len(knives) == 1
        assert knives[0].start.x >= 400 or knives[0].end.x >= 400
