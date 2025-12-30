"""
Tests for ezdxf adapter implementation.
"""
import pytest
from pathlib import Path
import tempfile

from src.infrastructure.dxf.ezdxf_adapter import EzdxfReader, EzdxfWriter
from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.types import LineCategory


class TestEzdxfReader:
    """Tests for EzdxfReader."""

    @pytest.fixture
    def reader(self) -> EzdxfReader:
        """Create an EzdxfReader instance."""
        return EzdxfReader()

    @pytest.fixture
    def sample_dxf(self, tmp_path: Path) -> Path:
        """Create a sample DXF file for testing."""
        import ezdxf

        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        # Add a line
        msp.add_line((0, 0), (100, 0), dxfattribs={'layer': 'CUT', 'color': 1})

        # Add another line
        msp.add_line((0, 50), (100, 50), dxfattribs={'layer': 'CREASE', 'color': 5})

        # Add an arc
        msp.add_arc(
            center=(50, 100),
            radius=25,
            start_angle=0,
            end_angle=180,
            dxfattribs={'layer': 'CUT', 'color': 1}
        )

        file_path = tmp_path / "test.dxf"
        doc.saveas(file_path)
        return file_path

    def test_read_file(self, reader: EzdxfReader, sample_dxf: Path) -> None:
        """Test reading a DXF file."""
        entities = reader.read(sample_dxf)
        assert len(entities) == 3

    def test_read_lines(self, reader: EzdxfReader, sample_dxf: Path) -> None:
        """Test that lines are correctly parsed."""
        entities = reader.read(sample_dxf)
        lines = [e for e in entities if isinstance(e, Line)]
        assert len(lines) == 2

        # Check first line
        line1 = lines[0]
        assert line1.start.x == 0.0
        assert line1.start.y == 0.0
        assert line1.end.x == 100.0
        assert line1.end.y == 0.0

    def test_read_arcs(self, reader: EzdxfReader, sample_dxf: Path) -> None:
        """Test that arcs are correctly parsed."""
        entities = reader.read(sample_dxf)
        arcs = [e for e in entities if isinstance(e, Arc)]
        assert len(arcs) == 1

        arc = arcs[0]
        assert arc.center.x == 50.0
        assert arc.center.y == 100.0
        assert arc.radius == 25.0

    def test_read_layer_info(self, reader: EzdxfReader, sample_dxf: Path) -> None:
        """Test that layer information is preserved."""
        entities = reader.read(sample_dxf)
        layers = {e.layer for e in entities}
        assert 'CUT' in layers
        assert 'CREASE' in layers

    def test_read_color_info(self, reader: EzdxfReader, sample_dxf: Path) -> None:
        """Test that color information is preserved."""
        entities = reader.read(sample_dxf)
        colors = {e.color for e in entities}
        assert 1 in colors  # Red (CUT)
        assert 5 in colors  # Blue (CREASE)

    def test_read_nonexistent_file(self, reader: EzdxfReader) -> None:
        """Test reading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            reader.read(Path("/nonexistent/file.dxf"))

    def test_get_file_info(self, reader: EzdxfReader, sample_dxf: Path) -> None:
        """Test getting file info."""
        info = reader.get_file_info(sample_dxf)
        assert 'version' in info
        assert 'entity_count' in info
        assert info['entity_count'] == 3


class TestEzdxfWriter:
    """Tests for EzdxfWriter."""

    @pytest.fixture
    def writer(self) -> EzdxfWriter:
        """Create an EzdxfWriter instance."""
        return EzdxfWriter()

    @pytest.fixture
    def reader(self) -> EzdxfReader:
        """Create an EzdxfReader instance for verification."""
        return EzdxfReader()

    def test_write_empty_file(self, writer: EzdxfWriter, tmp_path: Path) -> None:
        """Test writing an empty DXF file."""
        file_path = tmp_path / "empty.dxf"
        writer.write([], file_path)
        assert file_path.exists()

    def test_write_single_line(
        self,
        writer: EzdxfWriter,
        reader: EzdxfReader,
        tmp_path: Path
    ) -> None:
        """Test writing a single line."""
        line = Line(
            start=Point(0.0, 0.0),
            end=Point(100.0, 50.0),
            layer="TEST",
            color=1
        )

        file_path = tmp_path / "single_line.dxf"
        writer.write([line], file_path)

        # Verify by reading back
        entities = reader.read(file_path)
        assert len(entities) == 1
        assert isinstance(entities[0], Line)
        assert entities[0].start.x == 0.0
        assert entities[0].end.x == 100.0

    def test_write_multiple_entities(
        self,
        writer: EzdxfWriter,
        reader: EzdxfReader,
        tmp_path: Path
    ) -> None:
        """Test writing multiple entities."""
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), layer="CUT", color=1),
            Line(start=Point(0, 50), end=Point(100, 50), layer="CREASE", color=5),
            Arc(center=Point(50, 100), radius=25, start_angle=0, end_angle=180)
        ]

        file_path = tmp_path / "multiple.dxf"
        writer.write(entities, file_path)

        # Verify
        read_entities = reader.read(file_path)
        assert len(read_entities) == 3

    def test_write_preserves_layer(
        self,
        writer: EzdxfWriter,
        reader: EzdxfReader,
        tmp_path: Path
    ) -> None:
        """Test that layer info is preserved after write/read."""
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            layer="MY_LAYER",
            color=3
        )

        file_path = tmp_path / "layer_test.dxf"
        writer.write([line], file_path)

        entities = reader.read(file_path)
        assert entities[0].layer == "MY_LAYER"

    def test_write_preserves_color(
        self,
        writer: EzdxfWriter,
        reader: EzdxfReader,
        tmp_path: Path
    ) -> None:
        """Test that color info is preserved after write/read."""
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            layer="0",
            color=6  # Magenta
        )

        file_path = tmp_path / "color_test.dxf"
        writer.write([line], file_path)

        entities = reader.read(file_path)
        assert entities[0].color == 6

    def test_write_arc(
        self,
        writer: EzdxfWriter,
        reader: EzdxfReader,
        tmp_path: Path
    ) -> None:
        """Test writing and reading back an arc."""
        arc = Arc(
            center=Point(100, 100),
            radius=50,
            start_angle=45,
            end_angle=135,
            layer="ARC_LAYER"
        )

        file_path = tmp_path / "arc_test.dxf"
        writer.write([arc], file_path)

        entities = reader.read(file_path)
        assert len(entities) == 1
        assert isinstance(entities[0], Arc)
        read_arc = entities[0]
        assert read_arc.center.x == 100.0
        assert read_arc.center.y == 100.0
        assert read_arc.radius == 50.0


class TestRoundTrip:
    """Test round-trip read/write/read consistency."""

    def test_line_roundtrip(self, tmp_path: Path) -> None:
        """Test line survives roundtrip."""
        reader = EzdxfReader()
        writer = EzdxfWriter()

        original = Line(
            start=Point(10.5, 20.5),
            end=Point(110.5, 120.5),
            layer="ROUNDTRIP",
            color=4,
            category=LineCategory.CUT
        )

        file_path = tmp_path / "roundtrip.dxf"
        writer.write([original], file_path)
        entities = reader.read(file_path)

        assert len(entities) == 1
        result = entities[0]
        assert isinstance(result, Line)
        assert abs(result.start.x - original.start.x) < 0.001
        assert abs(result.start.y - original.start.y) < 0.001
        assert abs(result.end.x - original.end.x) < 0.001
        assert abs(result.end.y - original.end.y) < 0.001
