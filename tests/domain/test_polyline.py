"""Tests for Polyline entity."""
from __future__ import annotations

import pytest
import math

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.entities.polyline import Polyline, PolylineVertex
from src.domain.types import LineCategory, StandardColor, EntityType


class TestPolylineVertex:
    """Test PolylineVertex value object."""

    def test_create_vertex(self) -> None:
        """Test creating a vertex."""
        vertex = PolylineVertex(x=10.0, y=20.0, bulge=0.0)

        assert vertex.x == 10.0
        assert vertex.y == 20.0
        assert vertex.bulge == 0.0

    def test_vertex_point_property(self) -> None:
        """Test getting vertex as point."""
        vertex = PolylineVertex(x=10.0, y=20.0)
        point = vertex.point

        assert point.x == 10.0
        assert point.y == 20.0

    def test_vertex_has_bulge(self) -> None:
        """Test checking for bulge."""
        vertex_no_bulge = PolylineVertex(x=0, y=0, bulge=0.0)
        vertex_with_bulge = PolylineVertex(x=0, y=0, bulge=0.5)

        assert vertex_no_bulge.has_bulge() is False
        assert vertex_with_bulge.has_bulge() is True


class TestPolylineCreation:
    """Test Polyline creation."""

    def test_create_polyline(self) -> None:
        """Test creating a polyline."""
        vertices = (
            PolylineVertex(0, 0),
            PolylineVertex(10, 0),
            PolylineVertex(10, 10),
        )
        polyline = Polyline(vertices=vertices)

        assert polyline.vertex_count == 3
        assert polyline.segment_count == 2
        assert polyline.closed is False

    def test_create_closed_polyline(self) -> None:
        """Test creating a closed polyline."""
        vertices = (
            PolylineVertex(0, 0),
            PolylineVertex(10, 0),
            PolylineVertex(10, 10),
        )
        polyline = Polyline(vertices=vertices, closed=True)

        assert polyline.segment_count == 3  # 3 sides of triangle

    def test_entity_type(self) -> None:
        """Test entity type property."""
        polyline = Polyline(vertices=(PolylineVertex(0, 0),))

        assert polyline.entity_type == EntityType.POLYLINE

    def test_from_points(self) -> None:
        """Test creating polyline from points."""
        points = [Point(0, 0), Point(10, 0), Point(10, 10)]
        polyline = Polyline.from_points(
            points,
            closed=True,
            layer="CUT",
            color=StandardColor.RED
        )

        assert polyline.vertex_count == 3
        assert polyline.closed is True
        assert polyline.layer == "CUT"
        assert polyline.color == StandardColor.RED

    def test_from_points_with_tuples(self) -> None:
        """Test creating polyline from tuple coordinates."""
        points = [(0, 0), (10, 0), (10, 10)]
        polyline = Polyline.from_points(points)

        assert polyline.vertex_count == 3


class TestPolylineProperties:
    """Test Polyline properties."""

    def test_start_point(self) -> None:
        """Test getting start point."""
        vertices = (
            PolylineVertex(5, 10),
            PolylineVertex(15, 20),
        )
        polyline = Polyline(vertices=vertices)

        assert polyline.start.x == 5
        assert polyline.start.y == 10

    def test_end_point(self) -> None:
        """Test getting end point."""
        vertices = (
            PolylineVertex(5, 10),
            PolylineVertex(15, 20),
        )
        polyline = Polyline(vertices=vertices)

        assert polyline.end.x == 15
        assert polyline.end.y == 20

    def test_bounding_box(self) -> None:
        """Test getting bounding box."""
        vertices = (
            PolylineVertex(0, 0),
            PolylineVertex(100, 50),
            PolylineVertex(50, 100),
        )
        polyline = Polyline(vertices=vertices)

        min_x, min_y, max_x, max_y = polyline.get_bounding_box()

        assert min_x == 0
        assert min_y == 0
        assert max_x == 100
        assert max_y == 100

    def test_with_category(self) -> None:
        """Test creating copy with new category."""
        polyline = Polyline(
            vertices=(PolylineVertex(0, 0), PolylineVertex(10, 0)),
            category=LineCategory.UNKNOWN
        )

        new_polyline = polyline.with_category(LineCategory.CUT)

        assert new_polyline.category == LineCategory.CUT
        assert polyline.category == LineCategory.UNKNOWN  # Original unchanged


class TestPolylineDecompose:
    """Test Polyline decomposition."""

    def test_decompose_simple_polyline(self) -> None:
        """Test decomposing polyline with no bulges."""
        vertices = (
            PolylineVertex(0, 0),
            PolylineVertex(10, 0),
            PolylineVertex(10, 10),
        )
        polyline = Polyline(vertices=vertices, layer="CUT", color=StandardColor.RED)

        segments = polyline.decompose()

        assert len(segments) == 2
        assert all(isinstance(s, Line) for s in segments)

        # Check first segment
        assert segments[0].start.x == 0
        assert segments[0].end.x == 10
        assert segments[0].layer == "CUT"
        assert segments[0].color == StandardColor.RED

    def test_decompose_closed_polyline(self) -> None:
        """Test decomposing closed polyline."""
        vertices = (
            PolylineVertex(0, 0),
            PolylineVertex(10, 0),
            PolylineVertex(10, 10),
        )
        polyline = Polyline(vertices=vertices, closed=True)

        segments = polyline.decompose()

        assert len(segments) == 3  # Includes closing segment

    def test_decompose_with_bulge(self) -> None:
        """Test decomposing polyline with arc segment (bulge)."""
        # Create a polyline with a 90-degree arc
        # Bulge of 1.0 = 180 degree arc, 0.5 ~ 90 degree arc
        # bulge = tan(included_angle / 4)
        # For 90 degrees: tan(22.5) ≈ 0.414
        vertices = (
            PolylineVertex(0, 0, bulge=0.414),  # Arc to next vertex
            PolylineVertex(10, 0),
            PolylineVertex(20, 0),
        )
        polyline = Polyline(vertices=vertices)

        segments = polyline.decompose()

        assert len(segments) == 2
        assert isinstance(segments[0], Arc)  # First segment is arc
        assert isinstance(segments[1], Line)  # Second segment is line

    def test_decompose_single_vertex(self) -> None:
        """Test decomposing polyline with single vertex."""
        polyline = Polyline(vertices=(PolylineVertex(0, 0),))

        segments = polyline.decompose()

        assert len(segments) == 0

    def test_decompose_empty_polyline(self) -> None:
        """Test decomposing empty polyline."""
        polyline = Polyline(vertices=())

        segments = polyline.decompose()

        assert len(segments) == 0


class TestPolylineArcFromBulge:
    """Test arc generation from bulge values."""

    def test_semicircle_from_bulge(self) -> None:
        """Test creating semicircle from bulge = 1.0."""
        vertices = (
            PolylineVertex(0, 0, bulge=1.0),  # 180 degree arc
            PolylineVertex(10, 0),
        )
        polyline = Polyline(vertices=vertices)

        segments = polyline.decompose()

        assert len(segments) == 1
        arc = segments[0]
        assert isinstance(arc, Arc)
        assert abs(arc.radius - 5.0) < 0.01  # Radius should be half the chord

    def test_negative_bulge_direction(self) -> None:
        """Test that negative bulge creates arc in opposite direction."""
        vertices_positive = (
            PolylineVertex(0, 0, bulge=0.5),
            PolylineVertex(10, 0),
        )
        vertices_negative = (
            PolylineVertex(0, 0, bulge=-0.5),
            PolylineVertex(10, 0),
        )

        segments_pos = Polyline(vertices=vertices_positive).decompose()
        segments_neg = Polyline(vertices=vertices_negative).decompose()

        arc_pos = segments_pos[0]
        arc_neg = segments_neg[0]

        assert isinstance(arc_pos, Arc)
        assert isinstance(arc_neg, Arc)
        # Arcs should have same radius but different center Y
        assert abs(arc_pos.radius - arc_neg.radius) < 0.01
        # Centers should be on opposite sides of the chord
        assert arc_pos.center.y * arc_neg.center.y < 0  # Different signs

    def test_quarter_circle_bulge(self) -> None:
        """Test creating quarter circle from bulge."""
        # For 90 degree arc: bulge = tan(90/4) = tan(22.5) ≈ 0.4142
        bulge = math.tan(math.radians(22.5))
        vertices = (
            PolylineVertex(0, 0, bulge=bulge),
            PolylineVertex(10, 0),
        )
        polyline = Polyline(vertices=vertices)

        segments = polyline.decompose()

        assert len(segments) == 1
        arc = segments[0]
        assert isinstance(arc, Arc)
        # Verify the arc is approximately 90 degrees
        angle_diff = abs(arc.end_angle - arc.start_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        assert abs(angle_diff - 90) < 5  # Allow some tolerance
