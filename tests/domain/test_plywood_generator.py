"""Tests for PlywoodGenerator domain service."""
from __future__ import annotations

import pytest

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.bounding_box import BoundingBox
from src.domain.services.plywood_generator import PlywoodGenerator, PlywoodSettings
from src.domain.types import PlateType, StandardColor


class TestPlywoodSettings:
    """Test PlywoodSettings value object."""

    def test_default_settings(self) -> None:
        """Test default plywood settings."""
        settings = PlywoodSettings()

        assert settings.top_margin == 55.0
        assert settings.left_margin == 25.0
        assert settings.right_margin == 25.0

    def test_copper_plate_bottom_margin(self) -> None:
        """Test bottom margin for copper plate."""
        settings = PlywoodSettings.for_plate_type(PlateType.COPPER)

        assert settings.bottom_margin == 25.0

    def test_auto_plate_bottom_margin(self) -> None:
        """Test bottom margin for auto plate."""
        settings = PlywoodSettings.for_plate_type(PlateType.AUTO)

        assert settings.bottom_margin == 15.0


class TestPlywoodGeneratorRectangle:
    """Test plywood rectangle generation."""

    def test_generate_rectangle_from_bbox(self) -> None:
        """Test generating plywood rectangle from bounding box."""
        generator = PlywoodGenerator()
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=80)

        lines = generator.generate_rectangle(bbox)

        # Should create 4 lines forming a rectangle
        assert len(lines) == 4

    def test_rectangle_lines_form_closed_shape(self) -> None:
        """Test that generated lines form a closed rectangle."""
        generator = PlywoodGenerator()
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=80)

        lines = generator.generate_rectangle(bbox)

        # Collect all endpoints
        points = set()
        for line in lines:
            points.add((line.start.x, line.start.y))
            points.add((line.end.x, line.end.y))

        # Should have exactly 4 corner points
        assert len(points) == 4

    def test_rectangle_has_correct_color(self) -> None:
        """Test that plywood lines have white color (ACI 7)."""
        generator = PlywoodGenerator()
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=80)

        lines = generator.generate_rectangle(bbox)

        for line in lines:
            assert line.color == StandardColor.WHITE

    def test_rectangle_has_correct_layer(self) -> None:
        """Test that plywood lines are on PLYWOOD layer."""
        generator = PlywoodGenerator()
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=80)

        lines = generator.generate_rectangle(bbox)

        for line in lines:
            assert line.layer == "PLYWOOD"


class TestPlywoodGeneratorWithMargins:
    """Test plywood generation with margins."""

    def test_apply_margins_expands_bbox(self) -> None:
        """Test that margins expand the bounding box."""
        generator = PlywoodGenerator()
        settings = PlywoodSettings(
            top_margin=55,
            bottom_margin=25,
            left_margin=25,
            right_margin=25
        )
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=80)

        expanded = generator.apply_margins(bbox, settings)

        assert expanded.min_x == -25  # 0 - left_margin
        assert expanded.min_y == -25  # 0 - bottom_margin
        assert expanded.max_x == 125  # 100 + right_margin
        assert expanded.max_y == 135  # 80 + top_margin

    def test_generate_with_margins(self) -> None:
        """Test generating plywood with margins applied."""
        generator = PlywoodGenerator()
        settings = PlywoodSettings(
            top_margin=55,
            bottom_margin=25,
            left_margin=25,
            right_margin=25
        )
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=80)

        lines = generator.generate_with_margins(bbox, settings)

        # Calculate expected dimensions
        expected_width = 100 + 25 + 25  # bbox width + left + right
        expected_height = 80 + 55 + 25  # bbox height + top + bottom

        # Verify rectangle dimensions
        min_x = min(line.start.x for line in lines)
        max_x = max(line.end.x for line in lines)
        min_y = min(line.start.y for line in lines)
        max_y = max(line.end.y for line in lines)

        actual_width = max_x - min_x
        actual_height = max_y - min_y

        assert actual_width == expected_width
        assert actual_height == expected_height


class TestPlywoodGeneratorForEntities:
    """Test plywood generation for entity lists."""

    def test_generate_for_entities(self) -> None:
        """Test generating plywood frame for entity list."""
        generator = PlywoodGenerator()
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0)),
            Line(start=Point(0, 0), end=Point(0, 80)),
        ]
        settings = PlywoodSettings.for_plate_type(PlateType.COPPER)

        plywood_lines = generator.generate_for_entities(entities, settings)

        assert len(plywood_lines) == 4
        for line in plywood_lines:
            assert line.layer == "PLYWOOD"

    def test_generate_for_empty_entities(self) -> None:
        """Test generating plywood for empty entity list."""
        generator = PlywoodGenerator()

        plywood_lines = generator.generate_for_entities([])

        assert plywood_lines == []


class TestPlywoodGeneratorPositioning:
    """Test plywood drawing positioning."""

    def test_calculate_drawing_position(self) -> None:
        """Test calculating position to center drawing in plywood."""
        generator = PlywoodGenerator()
        drawing_bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=80)
        settings = PlywoodSettings(
            top_margin=55,
            bottom_margin=25,
            left_margin=25,
            right_margin=25
        )

        position = generator.calculate_drawing_position(drawing_bbox, settings)

        # Drawing should be positioned so margins are correct
        # For left margin of 25, drawing min_x should be at -25 + 25 = 0
        assert position.x == 0
        # For bottom margin of 25, drawing min_y should be at -25 + 25 = 0
        assert position.y == 0
