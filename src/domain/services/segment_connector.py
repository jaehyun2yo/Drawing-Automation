"""Service for connecting arc segments."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.bounding_box import BoundingBox

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


@dataclass(frozen=True, slots=True)
class ConnectionCandidate:
    """A candidate connection between two entities."""

    entity_a: object
    entity_b: object
    point_a: Point
    point_b: Point
    distance: float

    @property
    def midpoint(self) -> Point:
        """Get midpoint between the two connection points."""
        return Point(
            x=(self.point_a.x + self.point_b.x) / 2,
            y=(self.point_a.y + self.point_b.y) / 2
        )


@dataclass(frozen=True, slots=True)
class ConnectionResult:
    """Result of segment connection operation."""

    connected_entities: list
    connection_count: int
    unconnected_entities: list


@dataclass
class SegmentConnector:
    """
    Service for finding and connecting nearby segment endpoints.

    Identifies pairs of entities whose endpoints are within a tolerance
    distance and optionally connects them.
    """

    # Default tolerance in mm
    tolerance: float = 0.1

    # Connection constraints
    same_layer_only: bool = True
    same_color_only: bool = True

    def find_connectable_pairs(
        self,
        entities: list[Entity]
    ) -> list[ConnectionCandidate]:
        """
        Find all pairs of entities that can be connected.

        Args:
            entities: List of entities to analyze

        Returns:
            List of ConnectionCandidate objects
        """
        candidates = []

        for i, entity_a in enumerate(entities):
            endpoints_a = self._get_endpoints(entity_a)
            if not endpoints_a:
                continue

            for j, entity_b in enumerate(entities):
                if j <= i:
                    continue

                # Check constraints
                if not self._can_connect(entity_a, entity_b):
                    continue

                endpoints_b = self._get_endpoints(entity_b)
                if not endpoints_b:
                    continue

                # Check all endpoint combinations
                for point_a in endpoints_a:
                    for point_b in endpoints_b:
                        distance = self._calculate_distance(point_a, point_b)
                        if 0 < distance <= self.tolerance:
                            candidates.append(ConnectionCandidate(
                                entity_a=entity_a,
                                entity_b=entity_b,
                                point_a=point_a,
                                point_b=point_b,
                                distance=distance
                            ))

        return candidates

    def connect_segments(
        self,
        entities: list[Entity]
    ) -> ConnectionResult:
        """
        Connect segments that have endpoints within tolerance.

        For LINE-LINE connections with collinear segments, merges into one line.
        For other cases, extends endpoints to meet at midpoint.

        Args:
            entities: List of entities to process

        Returns:
            ConnectionResult with connected entities
        """
        candidates = self.find_connectable_pairs(entities)

        if not candidates:
            return ConnectionResult(
                connected_entities=list(entities),
                connection_count=0,
                unconnected_entities=[]
            )

        # Track which entities have been modified
        modified = set()
        entity_map = {id(e): e for e in entities}
        result_entities = []
        connection_count = 0

        # Process each connection candidate
        for candidate in candidates:
            id_a = id(candidate.entity_a)
            id_b = id(candidate.entity_b)

            # Skip if either entity was already modified
            if id_a in modified or id_b in modified:
                continue

            # Try to connect the entities
            connected = self._connect_pair(
                entity_map.get(id_a, candidate.entity_a),
                entity_map.get(id_b, candidate.entity_b),
                candidate
            )

            if connected:
                modified.add(id_a)
                modified.add(id_b)
                result_entities.extend(connected)
                connection_count += 1

        # Add unmodified entities
        for entity in entities:
            if id(entity) not in modified:
                result_entities.append(entity)

        return ConnectionResult(
            connected_entities=result_entities,
            connection_count=connection_count,
            unconnected_entities=[]
        )

    def extend_to_meet(
        self,
        line_a: Line,
        line_b: Line,
        connection: ConnectionCandidate
    ) -> tuple[Line, Line]:
        """
        Extend two lines to meet at their connection point.

        Args:
            line_a: First line
            line_b: Second line
            connection: Connection information

        Returns:
            Tuple of extended lines
        """
        midpoint = connection.midpoint

        # Determine which endpoint of each line to extend
        new_line_a = self._extend_line_endpoint(line_a, connection.point_a, midpoint)
        new_line_b = self._extend_line_endpoint(line_b, connection.point_b, midpoint)

        return new_line_a, new_line_b

    def _get_endpoints(self, entity: Entity) -> list[Point]:
        """Get endpoints of an entity."""
        from src.domain.entities.line import Line
        from src.domain.entities.arc import Arc

        if isinstance(entity, Line):
            return [entity.start, entity.end]
        elif isinstance(entity, Arc):
            return [entity.start_point, entity.end_point]

        return []

    def _calculate_distance(self, p1: Point, p2: Point) -> float:
        """Calculate distance between two points."""
        return ((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5

    def _can_connect(self, entity_a: Entity, entity_b: Entity) -> bool:
        """Check if two entities can be connected based on constraints."""
        # Check layer constraint
        if self.same_layer_only:
            layer_a = getattr(entity_a, 'layer', None)
            layer_b = getattr(entity_b, 'layer', None)
            if layer_a and layer_b and layer_a.upper() != layer_b.upper():
                return False

        # Check color constraint
        if self.same_color_only:
            color_a = getattr(entity_a, 'color', None)
            color_b = getattr(entity_b, 'color', None)
            if color_a is not None and color_b is not None and color_a != color_b:
                return False

        return True

    def _connect_pair(
        self,
        entity_a: Entity,
        entity_b: Entity,
        connection: ConnectionCandidate
    ) -> list[Entity] | None:
        """
        Connect a pair of entities.

        Returns:
            List of resulting entities, or None if connection failed
        """
        from src.domain.entities.line import Line

        # For now, only handle LINE-LINE connections
        if isinstance(entity_a, Line) and isinstance(entity_b, Line):
            # Check if collinear (can merge into single line)
            if self._are_collinear(entity_a, entity_b):
                return [self._merge_lines(entity_a, entity_b)]
            else:
                # Extend to meet
                new_a, new_b = self.extend_to_meet(entity_a, entity_b, connection)
                return [new_a, new_b]

        return None

    def _are_collinear(self, line_a: Line, line_b: Line, tolerance: float = 0.01) -> bool:
        """Check if two lines are collinear (on the same infinite line)."""
        # For two lines to be collinear, all four points must be on the same line

        # Calculate direction vectors
        dx_a = line_a.end.x - line_a.start.x
        dy_a = line_a.end.y - line_a.start.y

        # Check if line_b's start point is on line_a's infinite line
        # Using cross product: if cross product is zero, points are collinear
        dx_b = line_b.start.x - line_a.start.x
        dy_b = line_b.start.y - line_a.start.y
        cross_start = abs(dx_a * dy_b - dy_a * dx_b)

        dx_b = line_b.end.x - line_a.start.x
        dy_b = line_b.end.y - line_a.start.y
        cross_end = abs(dx_a * dy_b - dy_a * dx_b)

        line_length = (dx_a ** 2 + dy_a ** 2) ** 0.5
        if line_length < tolerance:
            return False

        # Normalize by line length for tolerance check
        return (cross_start / line_length < tolerance and
                cross_end / line_length < tolerance)

    def _merge_lines(self, line_a: Line, line_b: Line) -> Line:
        """Merge two collinear lines into one."""
        # Find the two points that are farthest apart
        all_points = [line_a.start, line_a.end, line_b.start, line_b.end]

        max_dist = 0
        start_point = all_points[0]
        end_point = all_points[1]

        for i, p1 in enumerate(all_points):
            for p2 in all_points[i + 1:]:
                dist = self._calculate_distance(p1, p2)
                if dist > max_dist:
                    max_dist = dist
                    start_point = p1
                    end_point = p2

        return Line(
            start=start_point,
            end=end_point,
            color=line_a.color,
            layer=line_a.layer,
            category=getattr(line_a, 'category', None)
        )

    def _extend_line_endpoint(
        self,
        line: Line,
        old_point: Point,
        new_point: Point
    ) -> Line:
        """Extend a line by moving one endpoint to a new position."""
        # Determine which endpoint to move
        if self._calculate_distance(line.start, old_point) < 0.001:
            return Line(
                start=new_point,
                end=line.end,
                color=line.color,
                layer=line.layer,
                category=getattr(line, 'category', None)
            )
        else:
            return Line(
                start=line.start,
                end=new_point,
                color=line.color,
                layer=line.layer,
                category=getattr(line, 'category', None)
            )
