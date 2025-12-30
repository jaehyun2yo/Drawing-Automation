"""Tests for SegmentConnector service."""
from __future__ import annotations

import pytest

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.services.segment_connector import SegmentConnector, ConnectionCandidate
from src.domain.types import StandardColor


class TestFindConnectablePairs:
    """Test finding connectable pairs."""

    def test_find_close_endpoints(self) -> None:
        """Test finding lines with close endpoints."""
        connector = SegmentConnector(tolerance=0.1)

        line1 = Line(start=Point(0, 0), end=Point(100, 0))
        line2 = Line(start=Point(100.05, 0), end=Point(200, 0))  # 0.05mm gap

        candidates = connector.find_connectable_pairs([line1, line2])

        assert len(candidates) == 1
        assert candidates[0].distance == pytest.approx(0.05, abs=0.01)

    def test_no_connection_when_too_far(self) -> None:
        """Test no connection when distance exceeds tolerance."""
        connector = SegmentConnector(tolerance=0.1)

        line1 = Line(start=Point(0, 0), end=Point(100, 0))
        line2 = Line(start=Point(101, 0), end=Point(200, 0))  # 1mm gap

        candidates = connector.find_connectable_pairs([line1, line2])

        assert len(candidates) == 0

    def test_no_connection_when_same_point(self) -> None:
        """Test no connection when distance is zero (already connected)."""
        connector = SegmentConnector(tolerance=0.1)

        line1 = Line(start=Point(0, 0), end=Point(100, 0))
        line2 = Line(start=Point(100, 0), end=Point(200, 0))  # Exactly same point

        candidates = connector.find_connectable_pairs([line1, line2])

        # Distance is 0, which is not > 0
        assert len(candidates) == 0

    def test_multiple_connections(self) -> None:
        """Test finding multiple connections."""
        connector = SegmentConnector(tolerance=0.1)

        lines = [
            Line(start=Point(0, 0), end=Point(100, 0)),
            Line(start=Point(100.05, 0), end=Point(200, 0)),
            Line(start=Point(200.05, 0), end=Point(300, 0)),
        ]

        candidates = connector.find_connectable_pairs(lines)

        assert len(candidates) == 2


class TestLayerAndColorConstraints:
    """Test layer and color constraints."""

    def test_same_layer_only(self) -> None:
        """Test same layer constraint."""
        connector = SegmentConnector(tolerance=0.1, same_layer_only=True)

        line1 = Line(start=Point(0, 0), end=Point(100, 0), layer="CUT")
        line2 = Line(start=Point(100.05, 0), end=Point(200, 0), layer="CREASE")

        candidates = connector.find_connectable_pairs([line1, line2])

        assert len(candidates) == 0

    def test_same_layer_matches(self) -> None:
        """Test same layer match."""
        connector = SegmentConnector(tolerance=0.1, same_layer_only=True)

        line1 = Line(start=Point(0, 0), end=Point(100, 0), layer="CUT")
        line2 = Line(start=Point(100.05, 0), end=Point(200, 0), layer="CUT")

        candidates = connector.find_connectable_pairs([line1, line2])

        assert len(candidates) == 1

    def test_same_color_only(self) -> None:
        """Test same color constraint."""
        connector = SegmentConnector(tolerance=0.1, same_color_only=True)

        line1 = Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED)
        line2 = Line(start=Point(100.05, 0), end=Point(200, 0), color=StandardColor.BLUE)

        candidates = connector.find_connectable_pairs([line1, line2])

        assert len(candidates) == 0

    def test_same_color_matches(self) -> None:
        """Test same color match."""
        connector = SegmentConnector(tolerance=0.1, same_color_only=True)

        line1 = Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED)
        line2 = Line(start=Point(100.05, 0), end=Point(200, 0), color=StandardColor.RED)

        candidates = connector.find_connectable_pairs([line1, line2])

        assert len(candidates) == 1


class TestConnectSegments:
    """Test connecting segments."""

    def test_connect_collinear_lines(self) -> None:
        """Test merging collinear lines."""
        connector = SegmentConnector(tolerance=0.1, same_layer_only=False, same_color_only=False)

        line1 = Line(start=Point(0, 0), end=Point(100, 0))
        line2 = Line(start=Point(100.05, 0), end=Point(200, 0))

        result = connector.connect_segments([line1, line2])

        assert result.connection_count == 1
        # Collinear lines should merge into one
        assert len(result.connected_entities) == 1

        merged = result.connected_entities[0]
        # Check merged line spans full length
        min_x = min(merged.start.x, merged.end.x)
        max_x = max(merged.start.x, merged.end.x)
        assert min_x == pytest.approx(0, abs=0.1)
        assert max_x == pytest.approx(200, abs=0.1)

    def test_connect_non_collinear_lines(self) -> None:
        """Test extending non-collinear lines to meet."""
        connector = SegmentConnector(tolerance=0.1, same_layer_only=False, same_color_only=False)

        line1 = Line(start=Point(0, 0), end=Point(100, 0))
        line2 = Line(start=Point(100.05, 0.05), end=Point(100.05, 100))  # Vertical

        result = connector.connect_segments([line1, line2])

        assert result.connection_count == 1
        # Non-collinear lines stay as 2 but with endpoints adjusted
        assert len(result.connected_entities) == 2

    def test_no_modification_when_no_connections(self) -> None:
        """Test no modification when no connections found."""
        connector = SegmentConnector(tolerance=0.1)

        line1 = Line(start=Point(0, 0), end=Point(100, 0))
        line2 = Line(start=Point(200, 0), end=Point(300, 0))  # Too far

        result = connector.connect_segments([line1, line2])

        assert result.connection_count == 0
        assert len(result.connected_entities) == 2


class TestConnectionCandidate:
    """Test ConnectionCandidate class."""

    def test_midpoint(self) -> None:
        """Test midpoint calculation."""
        candidate = ConnectionCandidate(
            entity_a=None,
            entity_b=None,
            point_a=Point(100, 0),
            point_b=Point(100.1, 0),
            distance=0.1
        )

        midpoint = candidate.midpoint
        assert midpoint.x == pytest.approx(100.05, abs=0.01)
        assert midpoint.y == 0


class TestAreCollinear:
    """Test collinearity detection."""

    def test_horizontal_lines_collinear(self) -> None:
        """Test horizontal lines are collinear."""
        connector = SegmentConnector()

        line1 = Line(start=Point(0, 0), end=Point(100, 0))
        line2 = Line(start=Point(100.05, 0), end=Point(200, 0))

        assert connector._are_collinear(line1, line2) is True

    def test_vertical_lines_collinear(self) -> None:
        """Test vertical lines are collinear."""
        connector = SegmentConnector()

        line1 = Line(start=Point(0, 0), end=Point(0, 100))
        line2 = Line(start=Point(0, 100.05), end=Point(0, 200))

        assert connector._are_collinear(line1, line2) is True

    def test_perpendicular_lines_not_collinear(self) -> None:
        """Test perpendicular lines are not collinear."""
        connector = SegmentConnector()

        line1 = Line(start=Point(0, 0), end=Point(100, 0))
        line2 = Line(start=Point(100, 0), end=Point(100, 100))

        assert connector._are_collinear(line1, line2) is False

    def test_diagonal_lines_collinear(self) -> None:
        """Test diagonal collinear lines."""
        connector = SegmentConnector()

        line1 = Line(start=Point(0, 0), end=Point(100, 100))
        line2 = Line(start=Point(100.05, 100.05), end=Point(200, 200))

        assert connector._are_collinear(line1, line2) is True

    def test_parallel_but_offset_not_collinear(self) -> None:
        """Test parallel but offset lines are not collinear."""
        connector = SegmentConnector()

        line1 = Line(start=Point(0, 0), end=Point(100, 0))
        line2 = Line(start=Point(0, 10), end=Point(100, 10))  # Parallel but offset

        assert connector._are_collinear(line1, line2) is False
