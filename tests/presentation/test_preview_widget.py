"""Tests for PreviewWidget."""
from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter

from src.presentation.widgets.preview_widget import PreviewWidget
from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.entities.bounding_box import BoundingBox


class TestPreviewWidget:
    """Test cases for PreviewWidget."""

    def test_widget_creation(self, qtbot: QtBot) -> None:
        """Test preview widget can be created."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        assert widget is not None

    def test_widget_default_size(self, qtbot: QtBot) -> None:
        """Test preview widget has reasonable default size."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        # Minimum size should be at least 400x300
        assert widget.minimumWidth() >= 400
        assert widget.minimumHeight() >= 300

    def test_set_entities_empty(self, qtbot: QtBot) -> None:
        """Test setting empty entity list."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        widget.set_entities([])
        assert widget.entities == []

    def test_set_entities_with_lines(self, qtbot: QtBot) -> None:
        """Test setting entities with lines."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        lines = [
            Line(start=Point(0, 0), end=Point(100, 0)),
            Line(start=Point(0, 0), end=Point(0, 100)),
        ]
        widget.set_entities(lines)

        assert len(widget.entities) == 2

    def test_set_entities_triggers_update(self, qtbot: QtBot) -> None:
        """Test setting entities triggers widget update."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)
        widget.show()

        lines = [Line(start=Point(0, 0), end=Point(100, 0))]

        # This should not raise any errors
        widget.set_entities(lines)


class TestPreviewWidgetZoom:
    """Test cases for zoom functionality."""

    def test_initial_zoom_level(self, qtbot: QtBot) -> None:
        """Test initial zoom level is 1.0."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        assert widget.zoom_level == 1.0

    def test_zoom_in(self, qtbot: QtBot) -> None:
        """Test zoom in increases zoom level."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        initial_zoom = widget.zoom_level
        widget.zoom_in()

        assert widget.zoom_level > initial_zoom

    def test_zoom_out(self, qtbot: QtBot) -> None:
        """Test zoom out decreases zoom level."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        widget.zoom_in()  # First zoom in
        current_zoom = widget.zoom_level
        widget.zoom_out()

        assert widget.zoom_level < current_zoom

    def test_zoom_has_minimum_limit(self, qtbot: QtBot) -> None:
        """Test zoom level has minimum limit."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        # Zoom out many times
        for _ in range(20):
            widget.zoom_out()

        assert widget.zoom_level >= 0.1  # Minimum zoom

    def test_zoom_has_maximum_limit(self, qtbot: QtBot) -> None:
        """Test zoom level has maximum limit."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        # Zoom in many times
        for _ in range(20):
            widget.zoom_in()

        assert widget.zoom_level <= 10.0  # Maximum zoom

    def test_zoom_to_fit(self, qtbot: QtBot) -> None:
        """Test zoom to fit adjusts zoom to show all entities."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        # Add some entities
        lines = [
            Line(start=Point(0, 0), end=Point(100, 0)),
            Line(start=Point(0, 0), end=Point(0, 100)),
        ]
        widget.set_entities(lines)
        widget.zoom_to_fit()

        # Zoom should be adjusted (not necessarily 1.0)
        assert widget.zoom_level > 0

    def test_reset_view(self, qtbot: QtBot) -> None:
        """Test reset view restores default zoom and pan."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        widget.zoom_in()
        widget.zoom_in()
        widget.reset_view()

        assert widget.zoom_level == 1.0
        assert widget.pan_offset == QPointF(0, 0)


class TestPreviewWidgetPan:
    """Test cases for pan functionality."""

    def test_initial_pan_offset(self, qtbot: QtBot) -> None:
        """Test initial pan offset is (0, 0)."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        assert widget.pan_offset == QPointF(0, 0)

    def test_pan_by_offset(self, qtbot: QtBot) -> None:
        """Test panning by offset changes pan position."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        widget.pan_by(50, 30)

        assert widget.pan_offset.x() == 50
        assert widget.pan_offset.y() == 30


class TestPreviewWidgetDisplay:
    """Test cases for display settings."""

    def test_background_color_default(self, qtbot: QtBot) -> None:
        """Test default background color is set."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        # Should have a background color property
        assert hasattr(widget, 'background_color')

    def test_show_grid_toggle(self, qtbot: QtBot) -> None:
        """Test grid visibility can be toggled."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        initial_state = widget.show_grid
        widget.toggle_grid()

        assert widget.show_grid != initial_state

    def test_antialias_enabled(self, qtbot: QtBot) -> None:
        """Test antialiasing is enabled by default."""
        widget = PreviewWidget()
        qtbot.addWidget(widget)

        assert widget.antialias_enabled is True
