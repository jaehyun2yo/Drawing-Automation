"""
Adobe Illustrator (.ai) file adapter for reading vector graphics.

Supports:
- SVG-based AI files
- PDF-based AI files (modern Illustrator)
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from src.application.ports.file_reader_port import IFileReader
from src.domain.entities.entity import Entity
from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.entities.polyline import Polyline as DomainPolyline, PolylineVertex
from src.domain.exceptions import AiParseError


class AiFileReader(IFileReader):
    """Reader for Adobe Illustrator (.ai) files."""

    # Default layer for imported entities
    DEFAULT_LAYER = "0"
    # Default color (white in AutoCAD color index)
    DEFAULT_COLOR = 7
    # Default linetype
    DEFAULT_LINETYPE = "CONTINUOUS"

    def read(self, file_path: Path) -> list[Entity]:
        """
        Read entities from an AI file.

        Args:
            file_path: Path to the AI file

        Returns:
            List of domain entities parsed from the file

        Raises:
            FileNotFoundError: If the file does not exist
            AiParseError: If the file cannot be parsed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"AI file not found: {file_path}")

        try:
            # Try to import svgpathtools
            import svgpathtools
        except ImportError as e:
            raise AiParseError(
                "svgpathtools library is required for AI file support. "
                "Install it with: pip install svgpathtools"
            ) from e

        file_type = self._detect_file_type(file_path)

        if file_type == "svg":
            return self._read_svg(file_path)
        elif file_type == "pdf":
            return self._read_pdf_based_ai(file_path)
        elif file_type == "eps":
            return self._read_eps(file_path)
        else:
            raise AiParseError(
                f"Unsupported AI file format. File appears to be: {file_type}"
            )

    def get_file_info(self, file_path: Path) -> dict[str, Any]:
        """
        Get metadata about an AI file.

        Args:
            file_path: Path to the AI file

        Returns:
            Dictionary with file info
        """
        if not file_path.exists():
            raise FileNotFoundError(f"AI file not found: {file_path}")

        file_type = self._detect_file_type(file_path)

        return {
            'format': 'Adobe Illustrator',
            'file_type': file_type,
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size,
        }

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Get list of supported file extensions."""
        return ['.ai', '.svg', '.eps']

    def _detect_file_type(self, file_path: Path) -> str:
        """
        Detect the actual format of an AI file.

        Args:
            file_path: Path to the file

        Returns:
            Format type: 'pdf', 'svg', 'eps', or 'unknown'
        """
        # Check file extension first
        suffix = file_path.suffix.lower()
        if suffix == '.svg':
            return 'svg'

        # Read file header to detect format
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)

            # Check for PDF header (modern AI files)
            if header.startswith(b'%PDF-'):
                return 'pdf'

            # Check for SVG/XML header
            if b'<?xml' in header or b'<svg' in header:
                return 'svg'

            # Check for EPS header
            if header.startswith(b'%!PS-Adobe') or header.startswith(b'%!PS'):
                return 'eps'

            # Default to SVG attempt for AI files
            return 'svg'

        except Exception:
            return 'unknown'

    def _read_svg(self, file_path: Path) -> list[Entity]:
        """
        Read entities from an SVG file using svgpathtools.

        Args:
            file_path: Path to the SVG file

        Returns:
            List of domain entities
        """
        import svgpathtools

        try:
            paths, attributes = svgpathtools.svg2paths(str(file_path))
        except Exception as e:
            raise AiParseError(f"Failed to parse SVG/AI file: {e}") from e

        entities: list[Entity] = []

        for path, attrs in zip(paths, attributes):
            # Extract layer from attributes if available
            layer = attrs.get('id', self.DEFAULT_LAYER)

            # Extract color from style or stroke
            color = self._extract_color(attrs)

            # Convert each segment in the path
            for segment in path:
                entity = self._convert_svg_segment(segment, layer, color)
                if entity is not None:
                    entities.append(entity)

        return entities

    def _read_pdf_based_ai(self, file_path: Path) -> list[Entity]:
        """
        Read entities from a PDF-based AI file using PyMuPDF.

        Args:
            file_path: Path to the PDF-based AI file

        Returns:
            List of domain entities
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            # Fallback: try svgpathtools anyway
            try:
                return self._read_svg(file_path)
            except Exception:
                raise AiParseError(
                    "PDF-based AI files require PyMuPDF library. "
                    "Install it with: pip install PyMuPDF"
                )

        try:
            doc = fitz.open(str(file_path))
        except Exception as e:
            raise AiParseError(f"Failed to open PDF-based AI file: {e}") from e

        entities: list[Entity] = []

        try:
            for page in doc:
                # Get all drawings (paths) from the page
                drawings = page.get_drawings()

                for drawing in drawings:
                    # Each drawing contains items (path segments)
                    items = drawing.get("items", [])
                    color = self._extract_pdf_color(drawing)

                    for item in items:
                        entity = self._convert_pdf_item(item, color)
                        if entity is not None:
                            entities.append(entity)
        finally:
            doc.close()

        return entities

    def _read_eps(self, file_path: Path) -> list[Entity]:
        """
        Read entities from an EPS-based AI file.

        EPS files are parsed by:
        1. Converting via Inkscape (if available) - most reliable
        2. Trying PyMuPDF (supports some EPS files)
        3. Parsing PostScript path commands directly (fallback)

        Args:
            file_path: Path to the EPS file

        Returns:
            List of domain entities
        """
        # First try Inkscape conversion (most reliable for AI files)
        try:
            entities = self._convert_via_inkscape(file_path)
            if entities:
                return entities
        except Exception:
            pass  # Inkscape not available or failed

        # Try PyMuPDF if available
        try:
            import fitz  # PyMuPDF
            try:
                doc = fitz.open(str(file_path))
                entities: list[Entity] = []

                for page in doc:
                    drawings = page.get_drawings()
                    for drawing in drawings:
                        items = drawing.get("items", [])
                        color = self._extract_pdf_color(drawing)
                        for item in items:
                            entity = self._convert_pdf_item(item, color)
                            if entity is not None:
                                entities.append(entity)

                doc.close()

                if entities:
                    return entities
            except Exception:
                pass  # Fall through to direct parsing
        except ImportError:
            pass  # PyMuPDF not installed

        # Direct EPS/PostScript path parsing (fallback)
        return self._parse_eps_paths(file_path)

    def _convert_via_inkscape(self, file_path: Path) -> list[Entity]:
        """
        Convert AI/EPS file to DXF using Inkscape, then read with ezdxf.

        Args:
            file_path: Path to the AI/EPS file

        Returns:
            List of domain entities
        """
        import subprocess
        import tempfile
        import shutil

        # Check if Inkscape is available
        inkscape_path = shutil.which('inkscape')
        if not inkscape_path:
            # Try common installation paths on Windows
            common_paths = [
                r'C:\Program Files\Inkscape\bin\inkscape.exe',
                r'C:\Program Files (x86)\Inkscape\bin\inkscape.exe',
            ]
            for path in common_paths:
                if Path(path).exists():
                    inkscape_path = path
                    break

        if not inkscape_path:
            raise FileNotFoundError("Inkscape not found")

        # Create temporary DXF file
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
            tmp_dxf_path = Path(tmp.name)

        try:
            # Convert AI/EPS to DXF using Inkscape
            result = subprocess.run(
                [
                    inkscape_path,
                    str(file_path),
                    '--export-filename=' + str(tmp_dxf_path),
                    '--export-type=dxf',
                ],
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"Inkscape conversion failed: {result.stderr}")

            # Read the converted DXF file
            from src.infrastructure.dxf.ezdxf_adapter import EzdxfReader
            reader = EzdxfReader()
            entities = reader.read(tmp_dxf_path)

            return entities

        finally:
            # Clean up temporary file
            if tmp_dxf_path.exists():
                tmp_dxf_path.unlink()

    def _parse_eps_paths(self, file_path: Path) -> list[Entity]:
        """
        Parse PostScript path commands from EPS file.

        Args:
            file_path: Path to the EPS file

        Returns:
            List of domain entities
        """
        import re

        entities: list[Entity] = []

        try:
            # Read file content (EPS files are typically ASCII)
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            raise AiParseError(f"Failed to read EPS file: {e}") from e

        # Parse PostScript path commands
        # Common patterns: x y moveto, x y lineto, x y x y x y curveto, closepath
        current_path: list[tuple[float, float]] = []
        current_x, current_y = 0.0, 0.0

        # Regex patterns for PostScript/AI commands
        # AI uses: m (moveto), L (lineto), C (curveto) - case sensitive!
        number = r'[-+]?(?:\d+\.?\d*|\.\d+)'

        # moveto: "x y m" or "x y moveto"
        moveto_pattern = re.compile(
            rf'({number})\s+({number})\s+[mM](?:oveto)?(?:\s|$)'
        )

        # lineto: "x y L" or "x y l" or "x y lineto"
        lineto_pattern = re.compile(
            rf'({number})\s+({number})\s+[lL](?:ineto)?(?:\s|$)'
        )

        # curveto: "x1 y1 x2 y2 x3 y3 c/C" or "curveto"
        curveto_pattern = re.compile(
            rf'({number})\s+({number})\s+({number})\s+({number})\s+'
            rf'({number})\s+({number})\s+[cCvV](?:urveto)?(?:\s|$)'
        )

        lines = content.split('\n')
        for line in lines:
            line = line.strip()

            # Skip comments and non-path data
            if line.startswith('%') or not line:
                continue

            # Parse moveto commands
            for match in moveto_pattern.finditer(line):
                # Save current path if exists
                if len(current_path) >= 2:
                    entities.extend(self._path_to_entities(current_path))
                current_x, current_y = float(match.group(1)), float(match.group(2))
                current_path = [(current_x, current_y)]

            # Parse lineto commands
            for match in lineto_pattern.finditer(line):
                x, y = float(match.group(1)), float(match.group(2))
                if current_path:
                    current_path.append((x, y))
                current_x, current_y = x, y

            # Parse curveto commands (Bezier curves)
            for match in curveto_pattern.finditer(line):
                x1, y1 = float(match.group(1)), float(match.group(2))
                x2, y2 = float(match.group(3)), float(match.group(4))
                x3, y3 = float(match.group(5)), float(match.group(6))

                # Sample the Bezier curve
                if current_path:
                    bezier_points = self._sample_bezier_coords(
                        current_x, current_y, x1, y1, x2, y2, x3, y3
                    )
                    current_path.extend(bezier_points[1:])  # Skip first (current point)

                current_x, current_y = x3, y3

            # Check for closepath or stroke/fill commands that end a path
            # AI commands: closepath, s/S (stroke), f/F (fill), b/B (fill+stroke), n/N (discard)
            line_lower = line.lower()
            is_path_end = (
                'closepath' in line_lower
                or line.strip() in ('s', 'S', 'f', 'F', 'b', 'B', 'n', 'N', 'h', 'H')
                or line.endswith(' s') or line.endswith(' S')
                or line.endswith(' f') or line.endswith(' F')
                or line.endswith(' b') or line.endswith(' B')
                or line.endswith(' n') or line.endswith(' N')
            )

            if is_path_end:
                if current_path and len(current_path) >= 2:
                    # Close the path if it's a closepath command
                    if 'closepath' in line_lower or line.strip() in ('s', 'f', 'b', 'h'):
                        if current_path[0] != current_path[-1]:
                            current_path.append(current_path[0])
                    entities.extend(self._path_to_entities(current_path))
                    current_path = []

        # Save any remaining path
        if len(current_path) >= 2:
            entities.extend(self._path_to_entities(current_path))

        if not entities:
            raise AiParseError(
                "AI 파일을 파싱할 수 없습니다.\n\n"
                "해결 방법:\n"
                "1. Inkscape 설치 (https://inkscape.org) - 자동 변환 지원\n"
                "2. Adobe Illustrator에서 DXF로 저장 후 열기\n"
                "3. AI 파일을 SVG로 저장 후 열기"
            )

        return entities

    def _sample_bezier_coords(
        self,
        x0: float, y0: float,
        x1: float, y1: float,
        x2: float, y2: float,
        x3: float, y3: float,
        num_segments: int = 10
    ) -> list[tuple[float, float]]:
        """Sample points along a cubic Bezier curve defined by coordinates."""
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            x = (
                (1 - t) ** 3 * x0
                + 3 * (1 - t) ** 2 * t * x1
                + 3 * (1 - t) * t ** 2 * x2
                + t ** 3 * x3
            )
            y = (
                (1 - t) ** 3 * y0
                + 3 * (1 - t) ** 2 * t * y1
                + 3 * (1 - t) * t ** 2 * y2
                + t ** 3 * y3
            )
            points.append((x, y))
        return points

    def _path_to_entities(
        self,
        path: list[tuple[float, float]]
    ) -> list[Entity]:
        """Convert a path (list of points) to domain entities."""
        entities: list[Entity] = []

        if len(path) < 2:
            return entities

        # Convert consecutive points to lines
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]

            # Skip zero-length lines
            if abs(x2 - x1) < 0.001 and abs(y2 - y1) < 0.001:
                continue

            entities.append(Line(
                start=Point(x1, y1),
                end=Point(x2, y2),
                layer=self.DEFAULT_LAYER,
                color=self.DEFAULT_COLOR,
                linetype=self.DEFAULT_LINETYPE
            ))

        return entities

    def _convert_svg_segment(
        self,
        segment: Any,
        layer: str,
        color: int
    ) -> Entity | None:
        """
        Convert an svgpathtools segment to a domain entity.

        Args:
            segment: svgpathtools segment (Line, Arc, CubicBezier, etc.)
            layer: Layer name
            color: Color index

        Returns:
            Domain entity or None if not supported
        """
        import svgpathtools

        if isinstance(segment, svgpathtools.Line):
            return self._convert_svg_line(segment, layer, color)
        elif isinstance(segment, svgpathtools.Arc):
            return self._convert_svg_arc(segment, layer, color)
        elif isinstance(segment, (svgpathtools.CubicBezier, svgpathtools.QuadraticBezier)):
            return self._convert_bezier_to_polyline(segment, layer, color)

        return None

    def _convert_svg_line(
        self,
        line: Any,
        layer: str,
        color: int
    ) -> Line:
        """Convert an svgpathtools Line to domain Line."""
        return Line(
            start=Point(line.start.real, line.start.imag),
            end=Point(line.end.real, line.end.imag),
            layer=layer,
            color=color,
            linetype=self.DEFAULT_LINETYPE
        )

    def _convert_svg_arc(
        self,
        arc: Any,
        layer: str,
        color: int
    ) -> Arc:
        """Convert an svgpathtools Arc to domain Arc."""
        # svgpathtools Arc uses complex numbers for points
        # and has center, radius, rotation, etc.

        # Get center and radius
        center = arc.center
        radius = arc.radius.real  # Assume circular arc

        # Calculate start and end angles
        start_point = arc.start
        end_point = arc.end

        start_angle = math.degrees(
            math.atan2(
                start_point.imag - center.imag,
                start_point.real - center.real
            )
        )
        end_angle = math.degrees(
            math.atan2(
                end_point.imag - center.imag,
                end_point.real - center.real
            )
        )

        return Arc(
            center=Point(center.real, center.imag),
            radius=radius,
            start_angle=start_angle,
            end_angle=end_angle,
            layer=layer,
            color=color,
            linetype=self.DEFAULT_LINETYPE
        )

    def _convert_bezier_to_polyline(
        self,
        bezier: Any,
        layer: str,
        color: int,
        num_segments: int = 10
    ) -> DomainPolyline:
        """
        Convert a Bezier curve to a polyline by sampling points.

        Args:
            bezier: svgpathtools CubicBezier or QuadraticBezier
            layer: Layer name
            color: Color index
            num_segments: Number of line segments to approximate the curve

        Returns:
            Domain Polyline
        """
        vertices = []

        for i in range(num_segments + 1):
            t = i / num_segments
            point = bezier.point(t)
            vertices.append(PolylineVertex(x=point.real, y=point.imag, bulge=0.0))

        return DomainPolyline(
            vertices=tuple(vertices),
            closed=False,
            layer=layer,
            color=color,
            linetype=self.DEFAULT_LINETYPE
        )

    def _convert_pdf_item(
        self,
        item: tuple,
        color: int
    ) -> Entity | None:
        """
        Convert a PyMuPDF drawing item to a domain entity.

        Args:
            item: PyMuPDF drawing item tuple
            color: Color index

        Returns:
            Domain entity or None if not supported
        """
        if not item:
            return None

        item_type = item[0]

        if item_type == "l":  # Line
            # Format: ("l", start_point, end_point)
            _, start, end = item
            return Line(
                start=Point(start.x, start.y),
                end=Point(end.x, end.y),
                layer=self.DEFAULT_LAYER,
                color=color,
                linetype=self.DEFAULT_LINETYPE
            )
        elif item_type == "c":  # Cubic Bezier curve
            # Format: ("c", p1, p2, p3, p4)
            # Approximate with polyline
            _, p1, p2, p3, p4 = item
            vertices = self._sample_cubic_bezier(p1, p2, p3, p4)
            return DomainPolyline(
                vertices=tuple(vertices),
                closed=False,
                layer=self.DEFAULT_LAYER,
                color=color,
                linetype=self.DEFAULT_LINETYPE
            )
        elif item_type == "re":  # Rectangle
            # Format: ("re", rect)
            _, rect = item
            # Convert rectangle to polyline
            vertices = [
                PolylineVertex(x=rect.x0, y=rect.y0, bulge=0.0),
                PolylineVertex(x=rect.x1, y=rect.y0, bulge=0.0),
                PolylineVertex(x=rect.x1, y=rect.y1, bulge=0.0),
                PolylineVertex(x=rect.x0, y=rect.y1, bulge=0.0),
            ]
            return DomainPolyline(
                vertices=tuple(vertices),
                closed=True,
                layer=self.DEFAULT_LAYER,
                color=color,
                linetype=self.DEFAULT_LINETYPE
            )

        return None

    def _sample_cubic_bezier(
        self,
        p1: Any,
        p2: Any,
        p3: Any,
        p4: Any,
        num_segments: int = 10
    ) -> list[PolylineVertex]:
        """
        Sample points along a cubic Bezier curve.

        Args:
            p1, p2, p3, p4: Control points
            num_segments: Number of segments

        Returns:
            List of PolylineVertex objects
        """
        vertices = []

        for i in range(num_segments + 1):
            t = i / num_segments
            # Cubic Bezier formula
            x = (
                (1 - t) ** 3 * p1.x
                + 3 * (1 - t) ** 2 * t * p2.x
                + 3 * (1 - t) * t ** 2 * p3.x
                + t ** 3 * p4.x
            )
            y = (
                (1 - t) ** 3 * p1.y
                + 3 * (1 - t) ** 2 * t * p2.y
                + 3 * (1 - t) * t ** 2 * p3.y
                + t ** 3 * p4.y
            )
            vertices.append(PolylineVertex(x=x, y=y, bulge=0.0))

        return vertices

    def _extract_color(self, attrs: dict) -> int:
        """
        Extract color from SVG attributes and convert to ACI.

        Args:
            attrs: SVG element attributes

        Returns:
            AutoCAD Color Index (1-255)
        """
        # Try to get stroke color
        stroke = attrs.get('stroke', '')
        style = attrs.get('style', '')

        # Parse style attribute for stroke
        if 'stroke:' in style:
            for part in style.split(';'):
                if part.strip().startswith('stroke:'):
                    stroke = part.split(':')[1].strip()
                    break

        # Convert common colors to ACI
        color_map = {
            'red': 1,
            '#ff0000': 1,
            'yellow': 2,
            '#ffff00': 2,
            'green': 3,
            '#00ff00': 3,
            'cyan': 4,
            '#00ffff': 4,
            'blue': 5,
            '#0000ff': 5,
            'magenta': 6,
            '#ff00ff': 6,
            'white': 7,
            '#ffffff': 7,
            'black': 7,  # Map black to white (visible on dark background)
            '#000000': 7,
        }

        stroke_lower = stroke.lower()
        return color_map.get(stroke_lower, self.DEFAULT_COLOR)

    def _extract_pdf_color(self, drawing: dict) -> int:
        """
        Extract color from PDF drawing and convert to ACI.

        Args:
            drawing: PyMuPDF drawing dict

        Returns:
            AutoCAD Color Index
        """
        # Get stroke color (RGB tuple)
        color = drawing.get('color')

        if color is None:
            return self.DEFAULT_COLOR

        # Convert RGB to approximate ACI
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            r, g, b = color[0], color[1], color[2]

            # Simple mapping to basic ACI colors
            if r > 0.7 and g < 0.3 and b < 0.3:
                return 1  # Red
            elif r > 0.7 and g > 0.7 and b < 0.3:
                return 2  # Yellow
            elif r < 0.3 and g > 0.7 and b < 0.3:
                return 3  # Green
            elif r < 0.3 and g > 0.7 and b > 0.7:
                return 4  # Cyan
            elif r < 0.3 and g < 0.3 and b > 0.7:
                return 5  # Blue
            elif r > 0.7 and g < 0.3 and b > 0.7:
                return 6  # Magenta

        return self.DEFAULT_COLOR
