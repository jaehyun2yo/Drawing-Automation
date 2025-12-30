"""
ezdxf adapter for DXF file operations.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.entities import (
    Line as DxfLine,
    Arc as DxfArc,
    LWPolyline as DxfLWPolyline,
    Polyline as DxfPolyline,
)

from src.application.ports.dxf_port import IDxfReader, IDxfWriter
from src.domain.entities.entity import Entity
from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.entities.polyline import Polyline as DomainPolyline, PolylineVertex
from src.domain.services.text_generator import TextEntity
from src.domain.exceptions import DxfParseError, DxfWriteError


class EzdxfReader(IDxfReader):
    """ezdxf implementation of IDxfReader."""

    def read(self, file_path: Path) -> list[Entity]:
        """
        Read entities from a DXF file.

        Args:
            file_path: Path to the DXF file

        Returns:
            List of domain entities parsed from the file

        Raises:
            FileNotFoundError: If the file does not exist
            DxfParseError: If the file cannot be parsed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"DXF file not found: {file_path}")

        try:
            doc = ezdxf.readfile(str(file_path))
        except Exception as e:
            raise DxfParseError(f"Failed to parse DXF file: {e}") from e

        entities: list[Entity] = []
        msp = doc.modelspace()

        for dxf_entity in msp:
            domain_entity = self._convert_entity(dxf_entity)
            if domain_entity is not None:
                entities.append(domain_entity)

        return entities

    def get_file_info(self, file_path: Path) -> dict[str, Any]:
        """
        Get metadata about a DXF file.

        Args:
            file_path: Path to the DXF file

        Returns:
            Dictionary with file info
        """
        if not file_path.exists():
            raise FileNotFoundError(f"DXF file not found: {file_path}")

        try:
            doc = ezdxf.readfile(str(file_path))
        except Exception as e:
            raise DxfParseError(f"Failed to parse DXF file: {e}") from e

        msp = doc.modelspace()
        entity_count = len(list(msp))

        return {
            'version': doc.dxfversion,
            'entity_count': entity_count,
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size,
        }

    def _convert_entity(self, dxf_entity: Any) -> Entity | None:
        """
        Convert a DXF entity to a domain entity.

        Args:
            dxf_entity: The ezdxf entity

        Returns:
            Domain entity or None if not supported
        """
        if isinstance(dxf_entity, DxfLine):
            return self._convert_line(dxf_entity)
        elif isinstance(dxf_entity, DxfArc):
            return self._convert_arc(dxf_entity)
        elif isinstance(dxf_entity, DxfLWPolyline):
            return self._convert_lwpolyline(dxf_entity)
        elif isinstance(dxf_entity, DxfPolyline):
            return self._convert_polyline(dxf_entity)
        return None

    def _convert_line(self, dxf_line: DxfLine) -> Line:
        """Convert a DXF LINE to domain Line."""
        start = dxf_line.dxf.start
        end = dxf_line.dxf.end

        return Line(
            start=Point(start.x, start.y),
            end=Point(end.x, end.y),
            layer=dxf_line.dxf.layer,  # default: "0"
            color=dxf_line.dxf.color,  # default: 256 (BYLAYER)
            linetype=dxf_line.dxf.linetype,  # default: "BYLAYER"
        )

    def _convert_arc(self, dxf_arc: DxfArc) -> Arc:
        """Convert a DXF ARC to domain Arc."""
        center = dxf_arc.dxf.center

        return Arc(
            center=Point(center.x, center.y),
            radius=dxf_arc.dxf.radius,
            start_angle=dxf_arc.dxf.start_angle,
            end_angle=dxf_arc.dxf.end_angle,
            layer=dxf_arc.dxf.layer,  # default: "0"
            color=dxf_arc.dxf.color,  # default: 256 (BYLAYER)
            linetype=dxf_arc.dxf.linetype,  # default: "BYLAYER"
        )

    def _convert_lwpolyline(self, dxf_lwpoly: DxfLWPolyline) -> DomainPolyline:
        """Convert a DXF LWPOLYLINE to domain Polyline."""
        # get_points with format='xyb' returns (x, y, bulge) tuples
        vertices = [
            PolylineVertex(x=x, y=y, bulge=bulge)
            for x, y, bulge in dxf_lwpoly.get_points(format='xyb')
        ]

        return DomainPolyline(
            vertices=tuple(vertices),
            closed=dxf_lwpoly.closed,  # property, not dxf attribute
            layer=dxf_lwpoly.dxf.layer,  # default: "0"
            color=dxf_lwpoly.dxf.color,  # default: 256 (BYLAYER)
            linetype=dxf_lwpoly.dxf.linetype,  # default: "BYLAYER"
        )

    def _convert_polyline(self, dxf_poly: DxfPolyline) -> DomainPolyline:
        """Convert a DXF POLYLINE (2D) to domain Polyline."""
        vertices = [
            PolylineVertex(
                x=vertex.dxf.location.x,
                y=vertex.dxf.location.y,
                bulge=vertex.dxf.get('bulge', 0.0),  # use get() with default
            )
            for vertex in dxf_poly.vertices
        ]

        return DomainPolyline(
            vertices=tuple(vertices),
            closed=dxf_poly.is_closed,  # property, not dxf attribute
            layer=dxf_poly.dxf.layer,  # default: "0"
            color=dxf_poly.dxf.color,  # default: 256 (BYLAYER)
            linetype=dxf_poly.dxf.linetype,  # default: "BYLAYER"
        )


class EzdxfWriter(IDxfWriter):
    """ezdxf implementation of IDxfWriter."""

    # DXF version mapping
    VERSION_MAP = {
        'AC1024': 'R2010',
        'AC1027': 'R2013',
        'AC1032': 'R2018',
        'AC1015': 'R2000',
        'AC1018': 'R2004',
        'AC1021': 'R2007',
        'AC1009': 'R12',
    }

    def write(
        self,
        entities: list[Entity],
        file_path: Path,
        version: str = "AC1024"
    ) -> None:
        """
        Write entities to a DXF file.

        Args:
            entities: List of domain entities to write
            file_path: Path to save the DXF file
            version: DXF version string (default: AC1024 = AutoCAD 2010)

        Raises:
            DxfWriteError: If the file cannot be written
        """
        # Convert version code to ezdxf format
        ezdxf_version = self.VERSION_MAP.get(version, 'R2010')

        try:
            doc = ezdxf.new(ezdxf_version)
            msp = doc.modelspace()

            # Ensure layers exist
            layers_used = {e.layer for e in entities if hasattr(e, 'layer')}
            for layer_name in layers_used:
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)

            # Add entities
            for entity in entities:
                self._add_entity(msp, entity)

            # Save file
            doc.saveas(str(file_path))

        except Exception as e:
            raise DxfWriteError(f"Failed to write DXF file: {e}") from e

    def _add_entity(self, msp: Any, entity: Entity) -> None:
        """
        Add a domain entity to the modelspace.

        Args:
            msp: ezdxf modelspace
            entity: Domain entity to add
        """
        if isinstance(entity, Line):
            self._add_line(msp, entity)
        elif isinstance(entity, Arc):
            self._add_arc(msp, entity)
        elif isinstance(entity, DomainPolyline):
            self._add_polyline(msp, entity)
        elif isinstance(entity, TextEntity):
            self._add_text(msp, entity)

    def _add_line(self, msp: Any, line: Line) -> None:
        """Add a Line entity to modelspace."""
        msp.add_line(
            start=(line.start.x, line.start.y),
            end=(line.end.x, line.end.y),
            dxfattribs={
                'layer': line.layer,
                'color': line.color,
                'linetype': line.linetype
            }
        )

    def _add_arc(self, msp: Any, arc: Arc) -> None:
        """Add an Arc entity to modelspace."""
        msp.add_arc(
            center=(arc.center.x, arc.center.y),
            radius=arc.radius,
            start_angle=arc.start_angle,
            end_angle=arc.end_angle,
            dxfattribs={
                'layer': arc.layer,
                'color': arc.color,
                'linetype': arc.linetype
            }
        )

    def _add_polyline(self, msp: Any, polyline: DomainPolyline) -> None:
        """Add a Polyline entity to modelspace as LWPOLYLINE."""
        # Convert vertices to format expected by ezdxf: (x, y, start_width, end_width, bulge)
        points = [
            (v.x, v.y, 0, 0, v.bulge) for v in polyline.vertices
        ]

        msp.add_lwpolyline(
            points,
            format='xyseb',
            close=polyline.closed,
            dxfattribs={
                'layer': polyline.layer,
                'color': polyline.color,
                'linetype': polyline.linetype
            }
        )

    def _add_text(self, msp: Any, text: TextEntity) -> None:
        """Add a Text entity to modelspace."""
        msp.add_text(
            text.content,
            dxfattribs={
                'insert': (text.position.x, text.position.y),
                'height': text.height,
                'rotation': text.rotation,
                'layer': text.layer,
                'color': text.color,
            }
        )
