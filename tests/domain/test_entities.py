"""
Tests for domain entities.
TDD: Tests written first, then implementation.
"""
import math
import pytest
from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.bounding_box import BoundingBox
from src.domain.entities.arc import Arc
from src.domain.entities.entity import Entity
from src.domain.types import LineCategory, EntityType


class TestPoint:
    """Tests for Point entity."""

    def test_create_point(self) -> None:
        """Test creating a point with x and y coordinates."""
        point = Point(10.0, 20.0)
        assert point.x == 10.0
        assert point.y == 20.0

    def test_point_equality(self) -> None:
        """Test that points with same coordinates are equal."""
        p1 = Point(10.0, 20.0)
        p2 = Point(10.0, 20.0)
        assert p1 == p2

    def test_point_inequality(self) -> None:
        """Test that points with different coordinates are not equal."""
        p1 = Point(10.0, 20.0)
        p2 = Point(10.0, 30.0)
        assert p1 != p2

    def test_point_distance_to(self) -> None:
        """Test calculating distance between two points."""
        p1 = Point(0.0, 0.0)
        p2 = Point(3.0, 4.0)
        assert p1.distance_to(p2) == 5.0

    def test_point_distance_to_same_point(self) -> None:
        """Test distance to same point is zero."""
        p1 = Point(10.0, 20.0)
        assert p1.distance_to(p1) == 0.0

    def test_point_midpoint(self) -> None:
        """Test calculating midpoint between two points."""
        p1 = Point(0.0, 0.0)
        p2 = Point(10.0, 10.0)
        midpoint = p1.midpoint_to(p2)
        assert midpoint.x == 5.0
        assert midpoint.y == 5.0

    def test_point_mirror_x(self) -> None:
        """Test mirroring a point across vertical axis."""
        point = Point(10.0, 20.0)
        mirrored = point.mirror_x(center_x=5.0)
        assert mirrored.x == 0.0
        assert mirrored.y == 20.0

    def test_point_translate(self) -> None:
        """Test translating a point by offset."""
        point = Point(10.0, 20.0)
        translated = point.translate(5.0, -10.0)
        assert translated.x == 15.0
        assert translated.y == 10.0

    def test_point_to_tuple(self) -> None:
        """Test converting point to tuple."""
        point = Point(10.0, 20.0)
        assert point.to_tuple() == (10.0, 20.0)

    def test_point_from_tuple(self) -> None:
        """Test creating point from tuple."""
        point = Point.from_tuple((10.0, 20.0))
        assert point.x == 10.0
        assert point.y == 20.0

    def test_point_immutable(self) -> None:
        """Test that point is immutable (frozen dataclass)."""
        point = Point(10.0, 20.0)
        with pytest.raises(AttributeError):
            point.x = 30.0  # type: ignore


class TestLine:
    """Tests for Line entity."""

    def test_create_line(self) -> None:
        """Test creating a line with start and end points."""
        start = Point(0.0, 0.0)
        end = Point(10.0, 0.0)
        line = Line(start=start, end=end)
        assert line.start == start
        assert line.end == end

    def test_line_length(self) -> None:
        """Test calculating line length."""
        line = Line(start=Point(0.0, 0.0), end=Point(3.0, 4.0))
        assert line.length == 5.0

    def test_line_length_horizontal(self) -> None:
        """Test horizontal line length."""
        line = Line(start=Point(0.0, 0.0), end=Point(100.0, 0.0))
        assert line.length == 100.0

    def test_line_length_vertical(self) -> None:
        """Test vertical line length."""
        line = Line(start=Point(0.0, 0.0), end=Point(0.0, 50.0))
        assert line.length == 50.0

    def test_line_midpoint(self) -> None:
        """Test getting line midpoint."""
        line = Line(start=Point(0.0, 0.0), end=Point(10.0, 10.0))
        midpoint = line.midpoint
        assert midpoint.x == 5.0
        assert midpoint.y == 5.0

    def test_line_is_horizontal(self) -> None:
        """Test detecting horizontal line."""
        line = Line(start=Point(0.0, 10.0), end=Point(100.0, 10.0))
        assert line.is_horizontal(tolerance=0.01)

    def test_line_is_vertical(self) -> None:
        """Test detecting vertical line."""
        line = Line(start=Point(10.0, 0.0), end=Point(10.0, 100.0))
        assert line.is_vertical(tolerance=0.01)

    def test_line_point_at_ratio(self) -> None:
        """Test getting point at specific ratio along line."""
        line = Line(start=Point(0.0, 0.0), end=Point(10.0, 0.0))
        point = line.point_at_ratio(0.5)
        assert point.x == 5.0
        assert point.y == 0.0

    def test_line_point_at_ratio_start(self) -> None:
        """Test ratio 0 returns start point."""
        line = Line(start=Point(10.0, 20.0), end=Point(30.0, 40.0))
        point = line.point_at_ratio(0.0)
        assert point == line.start

    def test_line_point_at_ratio_end(self) -> None:
        """Test ratio 1 returns end point."""
        line = Line(start=Point(10.0, 20.0), end=Point(30.0, 40.0))
        point = line.point_at_ratio(1.0)
        assert point == line.end

    def test_line_split_at_ratios(self) -> None:
        """Test splitting line at given ratios."""
        line = Line(start=Point(0.0, 0.0), end=Point(100.0, 0.0))
        segments = line.split_at_ratios([0.3, 0.7])
        assert len(segments) == 3
        assert segments[0].start.x == 0.0
        assert segments[0].end.x == 30.0
        assert segments[1].start.x == 30.0
        assert segments[1].end.x == 70.0
        assert segments[2].start.x == 70.0
        assert segments[2].end.x == 100.0

    def test_line_mirror_x(self) -> None:
        """Test mirroring line across vertical axis."""
        line = Line(start=Point(10.0, 0.0), end=Point(20.0, 10.0))
        mirrored = line.mirror_x(center_x=15.0)
        assert mirrored.start.x == 20.0
        assert mirrored.end.x == 10.0

    def test_line_translate(self) -> None:
        """Test translating line by offset."""
        line = Line(start=Point(0.0, 0.0), end=Point(10.0, 10.0))
        translated = line.translate(5.0, 5.0)
        assert translated.start.x == 5.0
        assert translated.start.y == 5.0
        assert translated.end.x == 15.0
        assert translated.end.y == 15.0

    def test_line_bounding_box(self) -> None:
        """Test getting line bounding box."""
        line = Line(start=Point(10.0, 20.0), end=Point(30.0, 50.0))
        bbox = line.bounding_box
        assert bbox.min_x == 10.0
        assert bbox.min_y == 20.0
        assert bbox.max_x == 30.0
        assert bbox.max_y == 50.0

    def test_line_default_category(self) -> None:
        """Test line default category is UNKNOWN."""
        line = Line(start=Point(0.0, 0.0), end=Point(10.0, 0.0))
        assert line.category == LineCategory.UNKNOWN

    def test_line_with_category(self) -> None:
        """Test line with specified category."""
        line = Line(
            start=Point(0.0, 0.0),
            end=Point(10.0, 0.0),
            category=LineCategory.CUT
        )
        assert line.category == LineCategory.CUT


class TestBoundingBox:
    """Tests for BoundingBox entity."""

    def test_create_bounding_box(self) -> None:
        """Test creating a bounding box."""
        bbox = BoundingBox(min_x=0.0, min_y=0.0, max_x=100.0, max_y=50.0)
        assert bbox.min_x == 0.0
        assert bbox.min_y == 0.0
        assert bbox.max_x == 100.0
        assert bbox.max_y == 50.0

    def test_bounding_box_width(self) -> None:
        """Test bounding box width calculation."""
        bbox = BoundingBox(min_x=10.0, min_y=20.0, max_x=110.0, max_y=70.0)
        assert bbox.width == 100.0

    def test_bounding_box_height(self) -> None:
        """Test bounding box height calculation."""
        bbox = BoundingBox(min_x=10.0, min_y=20.0, max_x=110.0, max_y=70.0)
        assert bbox.height == 50.0

    def test_bounding_box_center(self) -> None:
        """Test bounding box center point."""
        bbox = BoundingBox(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
        center = bbox.center
        assert center.x == 50.0
        assert center.y == 50.0

    def test_bounding_box_contains_point(self) -> None:
        """Test if bounding box contains a point."""
        bbox = BoundingBox(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
        assert bbox.contains_point(Point(50.0, 50.0))
        assert not bbox.contains_point(Point(150.0, 50.0))

    def test_bounding_box_contains_point_on_edge(self) -> None:
        """Test point on edge is contained."""
        bbox = BoundingBox(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
        assert bbox.contains_point(Point(0.0, 50.0))
        assert bbox.contains_point(Point(100.0, 50.0))

    def test_bounding_box_expand(self) -> None:
        """Test expanding bounding box by margin."""
        bbox = BoundingBox(min_x=10.0, min_y=10.0, max_x=90.0, max_y=90.0)
        expanded = bbox.expand(5.0)
        assert expanded.min_x == 5.0
        assert expanded.min_y == 5.0
        assert expanded.max_x == 95.0
        assert expanded.max_y == 95.0

    def test_bounding_box_union(self) -> None:
        """Test union of two bounding boxes."""
        bbox1 = BoundingBox(min_x=0.0, min_y=0.0, max_x=50.0, max_y=50.0)
        bbox2 = BoundingBox(min_x=30.0, min_y=30.0, max_x=100.0, max_y=100.0)
        union = bbox1.union(bbox2)
        assert union.min_x == 0.0
        assert union.min_y == 0.0
        assert union.max_x == 100.0
        assert union.max_y == 100.0

    def test_bounding_box_from_points(self) -> None:
        """Test creating bounding box from list of points."""
        points = [
            Point(10.0, 20.0),
            Point(50.0, 80.0),
            Point(30.0, 10.0),
        ]
        bbox = BoundingBox.from_points(points)
        assert bbox.min_x == 10.0
        assert bbox.min_y == 10.0
        assert bbox.max_x == 50.0
        assert bbox.max_y == 80.0

    def test_bounding_box_is_completely_outside(self) -> None:
        """Test detecting if bounding box is completely outside another."""
        outer = BoundingBox(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
        inside = BoundingBox(min_x=20.0, min_y=20.0, max_x=80.0, max_y=80.0)
        outside = BoundingBox(min_x=150.0, min_y=150.0, max_x=200.0, max_y=200.0)

        assert not inside.is_completely_outside(outer)
        assert outside.is_completely_outside(outer)


class TestArc:
    """Tests for Arc entity."""

    def test_create_arc(self) -> None:
        """Test creating an arc."""
        center = Point(50.0, 50.0)
        arc = Arc(
            center=center,
            radius=25.0,
            start_angle=0.0,
            end_angle=90.0
        )
        assert arc.center == center
        assert arc.radius == 25.0
        assert arc.start_angle == 0.0
        assert arc.end_angle == 90.0

    def test_arc_start_point(self) -> None:
        """Test getting arc start point."""
        arc = Arc(
            center=Point(0.0, 0.0),
            radius=10.0,
            start_angle=0.0,
            end_angle=90.0
        )
        start = arc.start_point
        assert abs(start.x - 10.0) < 0.0001
        assert abs(start.y - 0.0) < 0.0001

    def test_arc_end_point(self) -> None:
        """Test getting arc end point."""
        arc = Arc(
            center=Point(0.0, 0.0),
            radius=10.0,
            start_angle=0.0,
            end_angle=90.0
        )
        end = arc.end_point
        assert abs(end.x - 0.0) < 0.0001
        assert abs(end.y - 10.0) < 0.0001

    def test_arc_bounding_box(self) -> None:
        """Test getting arc bounding box."""
        arc = Arc(
            center=Point(0.0, 0.0),
            radius=10.0,
            start_angle=0.0,
            end_angle=90.0
        )
        bbox = arc.bounding_box
        assert bbox.min_x >= -0.0001
        assert bbox.min_y >= -0.0001
        assert abs(bbox.max_x - 10.0) < 0.0001
        assert abs(bbox.max_y - 10.0) < 0.0001

    def test_arc_mirror_x(self) -> None:
        """Test mirroring arc across vertical axis."""
        arc = Arc(
            center=Point(10.0, 0.0),
            radius=5.0,
            start_angle=0.0,
            end_angle=90.0
        )
        mirrored = arc.mirror_x(center_x=10.0)
        assert mirrored.center.x == 10.0
        # Angles should be adjusted for mirror


class TestEntity:
    """Tests for base Entity class."""

    def test_entity_type_line(self) -> None:
        """Test entity type for Line."""
        line = Line(start=Point(0.0, 0.0), end=Point(10.0, 0.0))
        assert line.entity_type == EntityType.LINE

    def test_entity_type_arc(self) -> None:
        """Test entity type for Arc."""
        arc = Arc(
            center=Point(0.0, 0.0),
            radius=10.0,
            start_angle=0.0,
            end_angle=90.0
        )
        assert arc.entity_type == EntityType.ARC
