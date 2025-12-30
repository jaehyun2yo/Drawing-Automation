"""Tests for GeometryService domain service."""
from __future__ import annotations

import pytest

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.entities.bounding_box import BoundingBox
from src.domain.services.geometry_service import GeometryService


class TestGeometryServiceBoundingBox:
    """Test bounding box calculations."""

    def test_bounding_box_single_line(self) -> None:
        """Test bounding box for a single line."""
        service = GeometryService()
        entities = [
            Line(start=Point(0, 0), end=Point(100, 50))
        ]

        bbox = service.calculate_bounding_box(entities)

        assert bbox.min_x == 0
        assert bbox.min_y == 0
        assert bbox.max_x == 100
        assert bbox.max_y == 50

    def test_bounding_box_multiple_lines(self) -> None:
        """Test bounding box for multiple lines."""
        service = GeometryService()
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0)),
            Line(start=Point(50, -20), end=Point(50, 80)),
        ]

        bbox = service.calculate_bounding_box(entities)

        assert bbox.min_x == 0
        assert bbox.min_y == -20
        assert bbox.max_x == 100
        assert bbox.max_y == 80

    def test_bounding_box_empty_list(self) -> None:
        """Test bounding box for empty entity list."""
        service = GeometryService()

        bbox = service.calculate_bounding_box([])

        assert bbox is None

    def test_bounding_box_with_arc(self) -> None:
        """Test bounding box includes arc extent."""
        service = GeometryService()
        entities = [
            Arc(center=Point(50, 50), radius=30, start_angle=0, end_angle=90)
        ]

        bbox = service.calculate_bounding_box(entities)

        # Arc from 0 to 90 degrees should extend from center to right and top
        assert bbox is not None
        assert bbox.min_x >= 50  # Right half of arc
        assert bbox.max_x <= 80  # Center + radius


class TestGeometryServiceMirror:
    """Test mirroring operations."""

    def test_mirror_line_x_axis(self) -> None:
        """Test mirroring a line across X axis."""
        service = GeometryService()
        line = Line(start=Point(10, 20), end=Point(30, 40))

        mirrored = service.mirror_x(line, center_x=50)

        assert mirrored.start.x == 90  # 50 + (50 - 10)
        assert mirrored.start.y == 20
        assert mirrored.end.x == 70  # 50 + (50 - 30)
        assert mirrored.end.y == 40

    def test_mirror_arc_x_axis(self) -> None:
        """Test mirroring an arc across X axis."""
        service = GeometryService()
        arc = Arc(center=Point(30, 50), radius=20, start_angle=0, end_angle=90)

        mirrored = service.mirror_x(arc, center_x=50)

        assert mirrored.center.x == 70  # 50 + (50 - 30)
        assert mirrored.center.y == 50
        # Angles should be mirrored
        assert mirrored.start_angle == 90  # 180 - 90
        assert mirrored.end_angle == 180  # 180 - 0

    def test_mirror_entities_list(self) -> None:
        """Test mirroring a list of entities."""
        service = GeometryService()
        entities = [
            Line(start=Point(0, 0), end=Point(20, 0)),
            Line(start=Point(0, 0), end=Point(0, 20)),
        ]

        mirrored = service.mirror_entities_x(entities, center_x=50)

        assert len(mirrored) == 2
        assert mirrored[0].start.x == 100  # 50 + (50 - 0)
        assert mirrored[1].start.x == 100


class TestGeometryServiceTranslate:
    """Test translation operations."""

    def test_translate_line(self) -> None:
        """Test translating a line."""
        service = GeometryService()
        line = Line(start=Point(10, 20), end=Point(30, 40))

        translated = service.translate(line, dx=5, dy=10)

        assert translated.start.x == 15
        assert translated.start.y == 30
        assert translated.end.x == 35
        assert translated.end.y == 50

    def test_translate_arc(self) -> None:
        """Test translating an arc."""
        service = GeometryService()
        arc = Arc(center=Point(50, 50), radius=20, start_angle=0, end_angle=90)

        translated = service.translate(arc, dx=-10, dy=5)

        assert translated.center.x == 40
        assert translated.center.y == 55
        assert translated.radius == 20

    def test_translate_entities_list(self) -> None:
        """Test translating a list of entities."""
        service = GeometryService()
        entities = [
            Line(start=Point(0, 0), end=Point(10, 0)),
            Arc(center=Point(5, 5), radius=3, start_angle=0, end_angle=180),
        ]

        translated = service.translate_entities(entities, dx=100, dy=50)

        assert len(translated) == 2
        assert translated[0].start.x == 100
        assert translated[0].start.y == 50
        assert translated[1].center.x == 105
        assert translated[1].center.y == 55


class TestGeometryServiceCenterAt:
    """Test centering operations."""

    def test_center_entities_at_origin(self) -> None:
        """Test centering entities at origin."""
        service = GeometryService()
        entities = [
            Line(start=Point(100, 100), end=Point(200, 200)),
        ]

        centered = service.center_at(entities, Point(0, 0))

        bbox = service.calculate_bounding_box(centered)
        center = bbox.center

        assert abs(center.x) < 0.01
        assert abs(center.y) < 0.01

    def test_center_entities_at_point(self) -> None:
        """Test centering entities at a specific point."""
        service = GeometryService()
        entities = [
            Line(start=Point(0, 0), end=Point(100, 100)),
        ]

        centered = service.center_at(entities, Point(500, 300))

        bbox = service.calculate_bounding_box(centered)
        center = bbox.center

        assert abs(center.x - 500) < 0.01
        assert abs(center.y - 300) < 0.01


class TestGeometryServiceDistances:
    """Test distance calculations."""

    def test_distance_between_points(self) -> None:
        """Test calculating distance between two points."""
        service = GeometryService()

        distance = service.distance(Point(0, 0), Point(3, 4))

        assert distance == 5.0

    def test_distance_same_point(self) -> None:
        """Test distance between same point is zero."""
        service = GeometryService()

        distance = service.distance(Point(10, 20), Point(10, 20))

        assert distance == 0.0
