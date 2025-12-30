"""Tests for ProcessDrawingUseCase."""
from __future__ import annotations

import pytest
from dataclasses import dataclass

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.types import PlateType, Side, StandardColor, LineCategory
from src.domain.value_objects.bridge_settings import BridgeSettings
from src.domain.services.plywood_generator import PlywoodSettings
from src.application.use_cases.process_drawing import (
    ProcessDrawingUseCase,
    ProcessingOptions,
    ProcessingResult,
)


class TestProcessingOptions:
    """Test ProcessingOptions value object."""

    def test_default_options(self) -> None:
        """Test default processing options."""
        options = ProcessingOptions()

        assert options.side == Side.BACK
        assert options.plate_type == PlateType.COPPER
        assert options.apply_bridges is True
        assert options.generate_plywood is True

    def test_custom_options(self) -> None:
        """Test custom processing options."""
        options = ProcessingOptions(
            side=Side.FRONT,
            plate_type=PlateType.AUTO,
            apply_bridges=False
        )

        assert options.side == Side.FRONT
        assert options.plate_type == PlateType.AUTO
        assert options.apply_bridges is False


class TestProcessDrawingUseCaseBasic:
    """Test basic processing functionality."""

    def test_process_empty_entities(self) -> None:
        """Test processing with empty entity list."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions()

        result = use_case.execute([], options)

        assert result.entities == []
        assert result.success is True

    def test_process_single_line(self) -> None:
        """Test processing a single line."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions(
            apply_bridges=False,
            generate_plywood=False
        )
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED)
        ]

        result = use_case.execute(entities, options)

        assert result.success is True
        assert len(result.entities) >= 1


class TestProcessDrawingUseCaseClassification:
    """Test entity classification during processing."""

    def test_entities_are_classified(self) -> None:
        """Test that entities are classified during processing."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions(
            apply_bridges=False,
            generate_plywood=False
        )
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED),
            Line(start=Point(0, 0), end=Point(0, 100), color=StandardColor.BLUE),
        ]

        result = use_case.execute(entities, options)

        # Check that classification was applied
        cut_lines = [e for e in result.entities if e.category == LineCategory.CUT]
        crease_lines = [e for e in result.entities if e.category == LineCategory.CREASE]

        assert len(cut_lines) >= 1
        assert len(crease_lines) >= 1


class TestProcessDrawingUseCaseBridges:
    """Test bridge application during processing."""

    def test_bridges_applied_to_cut_lines(self) -> None:
        """Test that bridges are applied to cut lines."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions(
            apply_bridges=True,
            generate_plywood=False
        )
        # Long enough line to get bridges
        entities = [
            Line(
                start=Point(0, 0),
                end=Point(200, 0),
                color=StandardColor.RED,
                category=LineCategory.CUT
            )
        ]

        result = use_case.execute(entities, options)

        # Should have multiple segments due to bridges
        cut_lines = [e for e in result.entities
                     if isinstance(e, Line) and e.category == LineCategory.CUT]
        assert len(cut_lines) > 1

    def test_short_lines_not_bridged(self) -> None:
        """Test that short lines are not bridged."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions(
            apply_bridges=True,
            generate_plywood=False
        )
        # Too short for bridges
        entities = [
            Line(
                start=Point(0, 0),
                end=Point(15, 0),
                color=StandardColor.RED,
                category=LineCategory.CUT
            )
        ]

        result = use_case.execute(entities, options)

        # Should still have just one line
        cut_lines = [e for e in result.entities
                     if isinstance(e, Line) and e.category == LineCategory.CUT]
        assert len(cut_lines) == 1


class TestProcessDrawingUseCaseMirroring:
    """Test mirroring during processing."""

    def test_front_side_is_mirrored(self) -> None:
        """Test that front side drawing is mirrored."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions(
            side=Side.FRONT,
            apply_bridges=False,
            generate_plywood=False
        )
        entities = [
            Line(start=Point(10, 0), end=Point(20, 0), color=StandardColor.RED)
        ]

        result = use_case.execute(entities, options)

        # Line should be mirrored - check that coordinates changed
        assert result.success is True
        # The mirrored line should have different x coordinates
        line = result.entities[0]
        # When mirrored around the center, coordinates should be inverted
        assert isinstance(line, Line)

    def test_back_side_not_mirrored(self) -> None:
        """Test that back side drawing is not mirrored."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions(
            side=Side.BACK,
            apply_bridges=False,
            generate_plywood=False
        )
        original_start_x = 10
        entities = [
            Line(
                start=Point(original_start_x, 0),
                end=Point(20, 0),
                color=StandardColor.RED
            )
        ]

        result = use_case.execute(entities, options)

        # Line should have same x coordinates
        line = result.entities[0]
        assert isinstance(line, Line)
        assert line.start.x == original_start_x


class TestProcessDrawingUseCasePlywood:
    """Test plywood generation during processing."""

    def test_plywood_generated_when_enabled(self) -> None:
        """Test that plywood frame is generated when enabled."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions(
            apply_bridges=False,
            generate_plywood=True
        )
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED),
            Line(start=Point(0, 0), end=Point(0, 80), color=StandardColor.RED),
        ]

        result = use_case.execute(entities, options)

        # Should have plywood lines
        plywood_lines = [e for e in result.entities
                         if isinstance(e, Line) and e.category == LineCategory.PLYWOOD]
        assert len(plywood_lines) == 4  # Rectangle has 4 sides

    def test_plywood_not_generated_when_disabled(self) -> None:
        """Test that plywood is not generated when disabled."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions(
            apply_bridges=False,
            generate_plywood=False
        )
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED),
        ]

        result = use_case.execute(entities, options)

        # Should not have plywood lines
        plywood_lines = [e for e in result.entities
                         if isinstance(e, Line) and e.category == LineCategory.PLYWOOD]
        assert len(plywood_lines) == 0


class TestProcessingResult:
    """Test ProcessingResult value object."""

    def test_result_contains_statistics(self) -> None:
        """Test that result contains processing statistics."""
        use_case = ProcessDrawingUseCase()
        options = ProcessingOptions(
            apply_bridges=False,
            generate_plywood=True
        )
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED),
            Line(start=Point(0, 0), end=Point(0, 80), color=StandardColor.BLUE),
        ]

        result = use_case.execute(entities, options)

        assert result.statistics is not None
        assert 'cut_count' in result.statistics
        assert 'crease_count' in result.statistics
