"""Tests for PolylineBridgeProcessor service."""
from __future__ import annotations

import pytest

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.polyline import Polyline, PolylineVertex
from src.domain.services.polyline_bridge_processor import (
    PolylineBridgeProcessor,
    PolylineProcessingResult,
)
from src.domain.value_objects.bridge_settings import BridgeSettings
from src.domain.types import LineCategory, StandardColor


class TestPolylineBridgeProcessorBasic:
    """Test basic PolylineBridgeProcessor functionality."""

    def test_process_empty_list(self) -> None:
        """Test processing empty entity list."""
        processor = PolylineBridgeProcessor()

        result = processor.process([])

        assert result.processed_entities == []
        assert result.original_polyline_count == 0
        assert result.decomposed_segment_count == 0

    def test_process_non_polyline_entities(self) -> None:
        """Test that non-polyline entities pass through unchanged."""
        processor = PolylineBridgeProcessor()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.RED
        )

        result = processor.process([line])

        assert len(result.processed_entities) == 1
        assert result.processed_entities[0] is line
        assert result.original_polyline_count == 0

    def test_decompose_polyline(self) -> None:
        """Test decomposing a polyline into segments."""
        processor = PolylineBridgeProcessor()
        polyline = Polyline.from_points(
            [Point(0, 0), Point(100, 0), Point(100, 100)],
            layer="CUT",
            color=StandardColor.RED,
            category=LineCategory.CUT,
        )

        result = processor.process([polyline], apply_bridges=False)

        assert result.original_polyline_count == 1
        assert result.decomposed_segment_count == 2
        assert len(result.processed_entities) == 2
        assert all(isinstance(e, Line) for e in result.processed_entities)


class TestPolylineBridgeProcessorWithBridges:
    """Test PolylineBridgeProcessor with bridge application."""

    def test_apply_bridges_to_long_segment(self) -> None:
        """Test applying bridges to long polyline segment."""
        processor = PolylineBridgeProcessor(
            cut_bridge_settings=BridgeSettings(
                gap_size=3.0,
                target_interval=50.0,
                min_length=10.0,
            )
        )
        # Create a polyline with one long segment (200mm)
        polyline = Polyline.from_points(
            [Point(0, 0), Point(200, 0)],
            category=LineCategory.CUT,
        )

        result = processor.process([polyline], apply_bridges=True)

        # Should have multiple segments due to bridges
        assert len(result.processed_entities) > 1
        assert result.bridged_segment_count >= 1

    def test_apply_crease_bridges(self) -> None:
        """Test applying crease bridges to polyline."""
        processor = PolylineBridgeProcessor(
            crease_bridge_settings=BridgeSettings(
                gap_size=2.0,
                target_interval=30.0,
                min_length=10.0,
            )
        )
        polyline = Polyline.from_points(
            [Point(0, 0), Point(100, 0)],
            category=LineCategory.CREASE,
        )

        result = processor.process([polyline], apply_bridges=True)

        # Should have segments with crease settings applied
        assert len(result.processed_entities) >= 1

    def test_no_bridges_for_auxiliary(self) -> None:
        """Test that auxiliary lines don't get bridges."""
        processor = PolylineBridgeProcessor()
        polyline = Polyline.from_points(
            [Point(0, 0), Point(200, 0)],
            category=LineCategory.AUXILIARY,
        )

        result = processor.process([polyline], apply_bridges=True)

        # Should not be split (no bridges)
        assert len(result.processed_entities) == 1
        assert result.bridged_segment_count == 0


class TestPolylineProcessingResult:
    """Test PolylineProcessingResult properties."""

    def test_total_output_count(self) -> None:
        """Test total output count property."""
        result = PolylineProcessingResult(
            processed_entities=[Line(Point(0, 0), Point(10, 0))] * 5,
            original_polyline_count=1,
            decomposed_segment_count=2,
            bridged_segment_count=1,
        )

        assert result.total_output_count == 5


class TestPolylineCounting:
    """Test polyline counting methods."""

    def test_get_polyline_count(self) -> None:
        """Test counting polylines in entity list."""
        processor = PolylineBridgeProcessor()
        entities = [
            Polyline.from_points([Point(0, 0), Point(10, 0)]),
            Line(Point(0, 0), Point(10, 0)),
            Polyline.from_points([Point(0, 0), Point(10, 0), Point(10, 10)]),
        ]

        count = processor.get_polyline_count(entities)

        assert count == 2

    def test_get_segment_count(self) -> None:
        """Test getting total segment count."""
        processor = PolylineBridgeProcessor()
        entities = [
            # Polyline with 2 segments
            Polyline.from_points([Point(0, 0), Point(10, 0), Point(10, 10)]),
            # Single line (1 segment)
            Line(Point(0, 0), Point(10, 0)),
            # Closed polyline with 3 segments
            Polyline.from_points([Point(0, 0), Point(10, 0), Point(10, 10)], closed=True),
        ]

        count = processor.get_segment_count(entities)

        assert count == 2 + 1 + 3  # = 6


class TestDecomposeOnly:
    """Test decompose_only method."""

    def test_decompose_without_bridges(self) -> None:
        """Test decomposing polylines without bridge application."""
        processor = PolylineBridgeProcessor()
        polyline = Polyline.from_points(
            [Point(0, 0), Point(200, 0)],  # Long segment that would get bridges
            category=LineCategory.CUT,
        )

        segments = processor.decompose_only([polyline])

        # Should have exactly one segment (no bridges)
        assert len(segments) == 1
        assert isinstance(segments[0], Line)


class TestMixedEntities:
    """Test processing mixed entity types."""

    def test_mixed_polylines_and_lines(self) -> None:
        """Test processing mix of polylines and regular lines."""
        processor = PolylineBridgeProcessor(
            cut_bridge_settings=BridgeSettings(
                gap_size=3.0,
                target_interval=50.0,
                min_length=10.0,
            )
        )
        entities = [
            Line(Point(0, 0), Point(50, 0), color=StandardColor.RED),
            Polyline.from_points(
                [Point(0, 10), Point(100, 10), Point(100, 60)],
                category=LineCategory.CUT,
            ),
            Line(Point(0, 20), Point(50, 20), color=StandardColor.BLUE),
        ]

        result = processor.process(entities, apply_bridges=False)

        # 1 line + 2 segments from polyline + 1 line = 4 entities
        assert len(result.processed_entities) == 4
        assert result.original_polyline_count == 1
        assert result.decomposed_segment_count == 2
