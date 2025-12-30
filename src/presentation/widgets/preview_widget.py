"""Preview widget for displaying DXF entities."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QWheelEvent, QMouseEvent
from PyQt6.QtWidgets import QWidget

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.entities.polyline import Polyline
from src.domain.types import StandardColor

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


class PreviewWidget(QWidget):
    """Widget for previewing DXF drawing entities."""

    # Zoom limits
    MIN_ZOOM = 0.1
    MAX_ZOOM = 10.0
    ZOOM_FACTOR = 1.2

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the preview widget."""
        super().__init__(parent)

        # Set minimum size
        self.setMinimumSize(400, 300)

        # Entity storage
        self._entities: list[Entity] = []

        # View state
        self._zoom_level = 1.0
        self._pan_offset = QPointF(0, 0)
        self._last_mouse_pos: QPointF | None = None

        # Display settings - CAD style (dark background)
        self._background_color = QColor(0, 0, 0)  # Black (CAD style)
        self._show_grid = True
        self._grid_color = QColor(50, 50, 50)  # Dark gray grid for dark background
        self._antialias_enabled = True

        # Enable mouse tracking for pan
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)

    @property
    def entities(self) -> list[Entity]:
        """Get current entities."""
        return self._entities

    @property
    def zoom_level(self) -> float:
        """Get current zoom level."""
        return self._zoom_level

    @property
    def pan_offset(self) -> QPointF:
        """Get current pan offset."""
        return self._pan_offset

    @property
    def background_color(self) -> QColor:
        """Get background color."""
        return self._background_color

    @property
    def show_grid(self) -> bool:
        """Get grid visibility state."""
        return self._show_grid

    @property
    def antialias_enabled(self) -> bool:
        """Get antialiasing state."""
        return self._antialias_enabled

    def set_entities(self, entities: list[Entity]) -> None:
        """Set entities to display."""
        self._entities = list(entities)
        self.update()

    def zoom_in(self) -> None:
        """Zoom in by zoom factor."""
        new_zoom = self._zoom_level * self.ZOOM_FACTOR
        self._zoom_level = min(new_zoom, self.MAX_ZOOM)
        self.update()

    def zoom_out(self) -> None:
        """Zoom out by zoom factor."""
        new_zoom = self._zoom_level / self.ZOOM_FACTOR
        self._zoom_level = max(new_zoom, self.MIN_ZOOM)
        self.update()

    def zoom_to_fit(self) -> None:
        """Adjust zoom to fit all entities in view."""
        if not self._entities:
            return

        # Calculate bounding box of all entities
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for entity in self._entities:
            bbox = entity.bounding_box
            min_x = min(min_x, bbox.min_x)
            min_y = min(min_y, bbox.min_y)
            max_x = max(max_x, bbox.max_x)
            max_y = max(max_y, bbox.max_y)

        if min_x == float('inf'):
            return

        # Calculate required zoom
        width = max_x - min_x
        height = max_y - min_y

        if width == 0 or height == 0:
            return

        # Add margin
        margin = 0.1
        zoom_x = self.width() * (1 - margin * 2) / width
        zoom_y = self.height() * (1 - margin * 2) / height

        self._zoom_level = min(zoom_x, zoom_y)
        self._zoom_level = max(self.MIN_ZOOM, min(self._zoom_level, self.MAX_ZOOM))

        # Center the view
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self._pan_offset = QPointF(
            self.width() / 2 - center_x * self._zoom_level,
            self.height() / 2 + center_y * self._zoom_level  # Flip Y
        )

        self.update()

    def reset_view(self) -> None:
        """Reset view to default zoom and pan."""
        self._zoom_level = 1.0
        self._pan_offset = QPointF(0, 0)
        self.update()

    def pan_by(self, dx: float, dy: float) -> None:
        """Pan view by offset."""
        self._pan_offset = QPointF(
            self._pan_offset.x() + dx,
            self._pan_offset.y() + dy
        )
        self.update()

    def toggle_grid(self) -> None:
        """Toggle grid visibility."""
        self._show_grid = not self._show_grid
        self.update()

    def paintEvent(self, event) -> None:
        """Paint the widget."""
        painter = QPainter(self)

        if self._antialias_enabled:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), self._background_color)

        # Draw grid if enabled
        if self._show_grid:
            self._draw_grid(painter)

        # Draw entities
        self._draw_entities(painter)

        painter.end()

    def _draw_grid(self, painter: QPainter) -> None:
        """Draw grid lines."""
        grid_pen = QPen(self._grid_color)
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)

        # Calculate grid spacing based on zoom
        base_spacing = 50
        spacing = base_spacing * self._zoom_level

        # Draw vertical lines
        start_x = int(self._pan_offset.x() % spacing)
        for x in range(start_x, self.width(), int(spacing)):
            painter.drawLine(x, 0, x, self.height())

        # Draw horizontal lines
        start_y = int(self._pan_offset.y() % spacing)
        for y in range(start_y, self.height(), int(spacing)):
            painter.drawLine(0, y, self.width(), y)

    def _draw_entities(self, painter: QPainter) -> None:
        """Draw all entities."""
        for entity in self._entities:
            color = self._get_entity_color(entity)
            pen = QPen(color)
            # Use thin pen (1 pixel) for better detail rendering
            pen.setWidth(1)
            painter.setPen(pen)

            if isinstance(entity, Line):
                self._draw_line(painter, entity)
            elif isinstance(entity, Arc):
                self._draw_arc(painter, entity)
            elif isinstance(entity, Polyline):
                self._draw_polyline(painter, entity)

    def _get_entity_color(self, entity: Entity) -> QColor:
        """Get display color for entity (CAD style - white on dark background)."""
        aci_color = getattr(entity, 'color', StandardColor.WHITE)

        # CAD style color mapping (for dark background)
        color_map = {
            StandardColor.RED: QColor(255, 0, 0),
            StandardColor.YELLOW: QColor(255, 255, 0),
            StandardColor.GREEN: QColor(0, 255, 0),
            StandardColor.CYAN: QColor(0, 255, 255),
            StandardColor.BLUE: QColor(0, 0, 255),
            StandardColor.MAGENTA: QColor(255, 0, 255),
            StandardColor.WHITE: QColor(255, 255, 255),
            StandardColor.BYLAYER: QColor(255, 255, 255),  # Default to white
            StandardColor.BYBLOCK: QColor(255, 255, 255),  # Default to white
        }

        return color_map.get(aci_color, QColor(255, 255, 255))

    def _transform_point(self, point: Point) -> QPointF:
        """Transform domain point to widget coordinates."""
        x = point.x * self._zoom_level + self._pan_offset.x()
        y = -point.y * self._zoom_level + self._pan_offset.y()  # Flip Y axis
        return QPointF(x, y)

    def _draw_line(self, painter: QPainter, line: Line) -> None:
        """Draw a line entity."""
        p1 = self._transform_point(line.start)
        p2 = self._transform_point(line.end)
        painter.drawLine(p1, p2)

    def _draw_arc(self, painter: QPainter, arc: Arc) -> None:
        """Draw an arc entity."""
        # Transform center
        center = self._transform_point(arc.center)
        radius = arc.radius * self._zoom_level

        # Calculate bounding rect for arc
        rect = QRectF(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2
        )

        # Calculate CCW span in world coordinates (handle 0°/360° boundary)
        world_span = arc.end_angle - arc.start_angle
        if world_span < 0:
            world_span += 360
        elif world_span == 0:
            world_span = 360  # Full circle

        # Convert angles (Qt uses 1/16th of a degree, counter-clockwise from 3 o'clock)
        # Qt's angle convention: 0° = 3 o'clock, 90° = 12 o'clock (up on screen)
        # This matches world coordinates, so no negation needed.
        # The Y-flip in _transform_point handles the coordinate transform,
        # but Qt's angle measurement is already screen-oriented (90° = up visually).
        start_angle = int(arc.start_angle * 16)
        span_angle = int(world_span * 16)

        painter.drawArc(rect, start_angle, span_angle)

    def _draw_polyline(self, painter: QPainter, polyline: Polyline) -> None:
        """Draw a polyline entity by decomposing into line/arc segments."""
        # Decompose polyline into individual segments
        segments = polyline.decompose()
        for segment in segments:
            if isinstance(segment, Line):
                self._draw_line(painter, segment)
            elif isinstance(segment, Arc):
                self._draw_arc(painter, segment)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zoom towards mouse position."""
        # Get mouse position in widget coordinates
        mouse_pos = event.position()

        # Calculate world coordinate under mouse (before zoom)
        world_x = (mouse_pos.x() - self._pan_offset.x()) / self._zoom_level
        world_y = -(mouse_pos.y() - self._pan_offset.y()) / self._zoom_level

        # Calculate new zoom level
        if event.angleDelta().y() > 0:
            new_zoom = self._zoom_level * self.ZOOM_FACTOR
            new_zoom = min(new_zoom, self.MAX_ZOOM)
        else:
            new_zoom = self._zoom_level / self.ZOOM_FACTOR
            new_zoom = max(new_zoom, self.MIN_ZOOM)

        # Adjust pan offset to keep the same world point under mouse
        self._pan_offset = QPointF(
            mouse_pos.x() - world_x * new_zoom,
            mouse_pos.y() + world_y * new_zoom
        )

        self._zoom_level = new_zoom
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for pan start."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._last_mouse_pos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for panning."""
        if self._last_mouse_pos is not None:
            delta = event.position() - self._last_mouse_pos
            self.pan_by(delta.x(), delta.y())
            self._last_mouse_pos = event.position()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release for pan end."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._last_mouse_pos = None
