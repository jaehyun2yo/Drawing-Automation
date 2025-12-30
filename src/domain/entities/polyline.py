"""Polyline entity for DXF polylines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator
from uuid import UUID, uuid4

from src.domain.entities.entity import Entity
from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.entities.bounding_box import BoundingBox
from src.domain.types import EntityType, LineCategory, StandardColor, ACIColor


@dataclass(frozen=True, slots=True)
class PolylineVertex:
    """A vertex in a polyline with optional bulge for arcs."""

    x: float
    y: float
    bulge: float = 0.0  # Bulge factor for arc segments (0 = straight line)

    @property
    def point(self) -> Point:
        """Get the vertex as a Point."""
        return Point(self.x, self.y)

    def has_bulge(self) -> bool:
        """Check if this vertex has a bulge (creates an arc to next vertex)."""
        return abs(self.bulge) > 1e-9


@dataclass
class Polyline(Entity):
    """
    Polyline entity representing a connected sequence of line/arc segments.

    A polyline consists of vertices, where each vertex can optionally have
    a bulge value that creates an arc to the next vertex.
    """

    vertices: tuple[PolylineVertex, ...] = field(default_factory=tuple)
    closed: bool = False

    # Inherited from Entity
    id: UUID = field(default_factory=uuid4, compare=False)
    layer: str = field(default="0")
    color: ACIColor = field(default=StandardColor.WHITE)
    linetype: str = field(default="CONTINUOUS")
    category: LineCategory = field(default=LineCategory.UNKNOWN)

    @property
    def entity_type(self) -> EntityType:
        """Get entity type."""
        return EntityType.POLYLINE

    @property
    def start(self) -> Point:
        """Get start point of polyline."""
        if not self.vertices:
            return Point(0, 0)
        return self.vertices[0].point

    @property
    def end(self) -> Point:
        """Get end point of polyline."""
        if not self.vertices:
            return Point(0, 0)
        return self.vertices[-1].point

    @property
    def vertex_count(self) -> int:
        """Get the number of vertices."""
        return len(self.vertices)

    @property
    def segment_count(self) -> int:
        """Get the number of segments."""
        if len(self.vertices) < 2:
            return 0
        count = len(self.vertices) - 1
        if self.closed:
            count += 1
        return count

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        """
        Get bounding box of polyline as tuple.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        if not self.vertices:
            return (0, 0, 0, 0)

        xs = [v.x for v in self.vertices]
        ys = [v.y for v in self.vertices]

        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def bounding_box(self) -> BoundingBox:
        """Calculate and return the bounding box of this polyline."""
        min_x, min_y, max_x, max_y = self.get_bounding_box()
        return BoundingBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)

    def mirror_x(self, center_x: float) -> "Polyline":
        """
        Create a new polyline mirrored across a vertical axis.

        Args:
            center_x: X coordinate of the mirror axis

        Returns:
            New polyline mirrored across the axis
        """
        mirrored_vertices = tuple(
            PolylineVertex(
                x=2 * center_x - v.x,
                y=v.y,
                bulge=-v.bulge  # Reverse bulge direction for mirroring
            )
            for v in self.vertices
        )
        return Polyline(
            vertices=mirrored_vertices,
            closed=self.closed,
            layer=self.layer,
            color=self.color,
            linetype=self.linetype,
            category=self.category,
        )

    def translate(self, dx: float, dy: float) -> "Polyline":
        """
        Create a new polyline translated by the given offset.

        Args:
            dx: X offset in millimeters
            dy: Y offset in millimeters

        Returns:
            New polyline translated by the offset
        """
        translated_vertices = tuple(
            PolylineVertex(
                x=v.x + dx,
                y=v.y + dy,
                bulge=v.bulge
            )
            for v in self.vertices
        )
        return Polyline(
            vertices=translated_vertices,
            closed=self.closed,
            layer=self.layer,
            color=self.color,
            linetype=self.linetype,
            category=self.category,
        )

    def decompose(self) -> list[Line | Arc]:
        """
        Decompose polyline into individual line and arc segments.

        This is essential for bridge processing, as bridges are applied
        to individual segments.

        Returns:
            List of Line and Arc entities representing the polyline segments
        """
        if len(self.vertices) < 2:
            return []

        segments: list[Line | Arc] = []
        vertex_pairs = list(self._get_vertex_pairs())

        for v1, v2 in vertex_pairs:
            if v1.has_bulge():
                # Create arc segment
                arc = self._create_arc_from_bulge(v1, v2)
                if arc:
                    segments.append(arc)
            else:
                # Create line segment
                segments.append(Line(
                    start=v1.point,
                    end=v2.point,
                    layer=self.layer,
                    color=self.color,
                    linetype=self.linetype,
                    category=self.category,
                ))

        return segments

    def _get_vertex_pairs(self) -> Iterator[tuple[PolylineVertex, PolylineVertex]]:
        """Generate pairs of consecutive vertices."""
        for i in range(len(self.vertices) - 1):
            yield (self.vertices[i], self.vertices[i + 1])

        if self.closed and len(self.vertices) > 1:
            yield (self.vertices[-1], self.vertices[0])

    def _create_arc_from_bulge(
        self,
        v1: PolylineVertex,
        v2: PolylineVertex
    ) -> Arc | None:
        """
        Create an arc from two vertices with bulge.

        The bulge factor is the tangent of 1/4 of the included angle.
        Positive bulge = counterclockwise arc
        Negative bulge = clockwise arc

        Args:
            v1: Start vertex with bulge
            v2: End vertex

        Returns:
            Arc entity or None if calculation fails
        """
        import math

        bulge = v1.bulge
        if abs(bulge) < 1e-9:
            return None

        # Calculate chord length and midpoint
        dx = v2.x - v1.x
        dy = v2.y - v1.y
        chord_length = math.sqrt(dx * dx + dy * dy)

        if chord_length < 1e-9:
            return None

        # Calculate arc parameters from bulge
        # bulge = tan(angle/4), so angle = 4 * atan(bulge)
        included_angle = 4 * math.atan(abs(bulge))

        # Radius: R = chord / (2 * sin(angle/2))
        half_angle = included_angle / 2
        radius = chord_length / (2 * math.sin(half_angle))

        # Sagitta (height of arc): s = R * (1 - cos(angle/2))
        sagitta = radius * (1 - math.cos(half_angle))

        # Find center point
        # The center is perpendicular to the chord at its midpoint
        mid_x = (v1.x + v2.x) / 2
        mid_y = (v1.y + v2.y) / 2

        # Unit vector along chord
        chord_ux = dx / chord_length
        chord_uy = dy / chord_length

        # Perpendicular vector (rotated 90 degrees CLOCKWISE)
        # This points to the RIGHT of the chord direction
        perp_ux = chord_uy
        perp_uy = -chord_ux

        # Distance from midpoint to center
        # For bulge > 0 (CCW arc): arc bulges LEFT, so center is to the RIGHT
        # For bulge < 0 (CW arc): arc bulges RIGHT, so center is to the LEFT
        dist_to_center = radius - sagitta
        if bulge < 0:
            dist_to_center = -dist_to_center

        center_x = mid_x + perp_ux * dist_to_center
        center_y = mid_y + perp_uy * dist_to_center

        # Calculate start and end angles
        start_angle = math.degrees(math.atan2(v1.y - center_y, v1.x - center_x))
        end_angle = math.degrees(math.atan2(v2.y - center_y, v2.x - center_x))

        # Normalize angles to 0-360
        if start_angle < 0:
            start_angle += 360
        if end_angle < 0:
            end_angle += 360

        # Ensure correct arc direction based on bulge sign
        # With center on the RIGHT of chord for positive bulge:
        # - Positive bulge (CCW): short arc is CW in angle terms, so swap to get CCW representation
        # - Negative bulge (CW): short arc is already CCW in angle terms, no swap needed
        if bulge > 0:
            start_angle, end_angle = end_angle, start_angle

        return Arc(
            center=Point(center_x, center_y),
            radius=abs(radius),
            start_angle=start_angle,
            end_angle=end_angle,
            layer=self.layer,
            color=self.color,
            linetype=self.linetype,
            category=self.category,
        )

    def with_category(self, category: LineCategory) -> Polyline:
        """Create a copy with a new category."""
        return Polyline(
            vertices=self.vertices,
            closed=self.closed,
            layer=self.layer,
            color=self.color,
            linetype=self.linetype,
            category=category,
        )

    @classmethod
    def from_points(
        cls,
        points: list[Point | tuple[float, float]],
        closed: bool = False,
        layer: str = "0",
        color: int = StandardColor.WHITE,
        linetype: str = "CONTINUOUS",
        category: LineCategory = LineCategory.UNKNOWN,
    ) -> Polyline:
        """
        Create a polyline from a list of points (no bulges).

        Args:
            points: List of points or (x, y) tuples
            closed: Whether the polyline is closed
            layer: Layer name
            color: ACI color
            linetype: Line type name
            category: Line category

        Returns:
            New Polyline instance
        """
        vertices = []
        for p in points:
            if isinstance(p, Point):
                vertices.append(PolylineVertex(p.x, p.y))
            else:
                vertices.append(PolylineVertex(p[0], p[1]))

        return cls(
            vertices=tuple(vertices),
            closed=closed,
            layer=layer,
            color=color,
            linetype=linetype,
            category=category,
        )
