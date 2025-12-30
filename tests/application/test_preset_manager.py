"""Tests for PresetManager."""
from __future__ import annotations

from pathlib import Path
import pytest
import tempfile
import json

from src.application.services.preset_manager import Preset, PresetManager
from src.domain.types import Side, PlateType


class TestPreset:
    """Test Preset data class."""

    def test_create_preset(self) -> None:
        """Test creating a preset with defaults."""
        preset = Preset(name="Test")

        assert preset.name == "Test"
        assert preset.side == Side.BACK
        assert preset.plate_type == PlateType.COPPER
        assert preset.cut_gap == 3.0
        assert preset.cut_interval == 60.0

    def test_to_dict(self) -> None:
        """Test converting preset to dictionary."""
        preset = Preset(
            name="Test",
            side=Side.FRONT,
            plate_type=PlateType.AUTO,
        )

        data = preset.to_dict()

        assert data["name"] == "Test"
        assert data["side"] == "FRONT"
        assert data["plate_type"] == "AUTO"

    def test_from_dict(self) -> None:
        """Test creating preset from dictionary."""
        data = {
            "name": "Test",
            "side": "FRONT",
            "plate_type": "AUTO",
            "cut_gap": 4.0,
        }

        preset = Preset.from_dict(data)

        assert preset.name == "Test"
        assert preset.side == Side.FRONT
        assert preset.plate_type == PlateType.AUTO
        assert preset.cut_gap == 4.0

    def test_get_paper_size_standard(self) -> None:
        """Test getting standard paper size."""
        preset = Preset(name="Test", paper_size_name="A3", use_custom_size=False)

        paper = preset.get_paper_size()

        assert paper.name == "A3"
        assert paper.width == 297
        assert paper.height == 420

    def test_get_paper_size_custom(self) -> None:
        """Test getting custom paper size."""
        preset = Preset(
            name="Test",
            custom_width=500,
            custom_height=700,
            use_custom_size=True
        )

        paper = preset.get_paper_size()

        assert paper.width == 500
        assert paper.height == 700

    def test_get_bridge_settings(self) -> None:
        """Test getting bridge settings from preset."""
        preset = Preset(
            name="Test",
            cut_gap=4.0,
            cut_interval=55.0,
            crease_gap=2.5,
            crease_interval=45.0,
        )

        cut_settings = preset.get_cut_bridge_settings()
        crease_settings = preset.get_crease_bridge_settings()

        assert cut_settings.gap_size == 4.0
        assert cut_settings.target_interval == 55.0
        assert crease_settings.gap_size == 2.5
        assert crease_settings.target_interval == 45.0


class TestPresetManager:
    """Test PresetManager service."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create a manager with temporary directory."""
        return PresetManager(presets_dir=temp_dir)

    def test_save_and_load_preset(self, manager: PresetManager) -> None:
        """Test saving and loading a preset."""
        preset = Preset(name="MyPreset", side=Side.FRONT)

        manager.save_preset(preset)
        loaded = manager.load_preset("MyPreset")

        assert loaded is not None
        assert loaded.name == "MyPreset"
        assert loaded.side == Side.FRONT

    def test_load_nonexistent_preset(self, manager: PresetManager) -> None:
        """Test loading a preset that doesn't exist."""
        loaded = manager.load_preset("NonExistent")

        assert loaded is None

    def test_load_default_preset(self, manager: PresetManager) -> None:
        """Test loading a built-in default preset."""
        loaded = manager.load_preset("기본값")

        assert loaded is not None
        assert loaded.name == "기본값"

    def test_delete_preset(self, manager: PresetManager, temp_dir: Path) -> None:
        """Test deleting a preset."""
        preset = Preset(name="ToDelete")
        manager.save_preset(preset)

        # Verify it exists
        assert manager.load_preset("ToDelete") is not None

        # Delete it
        result = manager.delete_preset("ToDelete")

        assert result is True
        assert manager.load_preset("ToDelete") is None

    def test_delete_nonexistent_preset(self, manager: PresetManager) -> None:
        """Test deleting a preset that doesn't exist."""
        result = manager.delete_preset("NonExistent")

        assert result is False

    def test_list_presets(self, manager: PresetManager) -> None:
        """Test listing all presets."""
        # Save a user preset
        manager.save_preset(Preset(name="UserPreset"))

        names = manager.list_presets()

        # Should include default presets and user preset
        assert "기본값" in names
        assert "UserPreset" in names

    def test_get_default_preset(self, manager: PresetManager) -> None:
        """Test getting the default preset."""
        preset = manager.get_default_preset()

        assert preset.name == "기본값"


class TestPresetExportImport:
    """Test preset export/import functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create a manager with temporary directory."""
        return PresetManager(presets_dir=temp_dir)

    def test_export_preset(self, manager: PresetManager, temp_dir: Path) -> None:
        """Test exporting a preset."""
        preset = Preset(name="ExportTest", side=Side.FRONT)
        manager.save_preset(preset)

        export_path = temp_dir / "exported.json"
        result = manager.export_preset("ExportTest", export_path)

        assert result is True
        assert export_path.exists()

        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["name"] == "ExportTest"
        assert data["side"] == "FRONT"

    def test_export_nonexistent_preset(self, manager: PresetManager, temp_dir: Path) -> None:
        """Test exporting a preset that doesn't exist."""
        export_path = temp_dir / "exported.json"
        result = manager.export_preset("NonExistent", export_path)

        assert result is False
        assert not export_path.exists()

    def test_import_preset(self, manager: PresetManager, temp_dir: Path) -> None:
        """Test importing a preset."""
        # Create a preset file
        import_path = temp_dir / "import_test.json"
        data = {
            "name": "ImportedPreset",
            "side": "FRONT",
            "plate_type": "AUTO",
        }
        with open(import_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Import it
        preset = manager.import_preset(import_path)

        assert preset is not None
        assert preset.name == "ImportedPreset"
        assert preset.side == Side.FRONT

        # Should now be loadable
        loaded = manager.load_preset("ImportedPreset")
        assert loaded is not None

    def test_import_nonexistent_file(self, manager: PresetManager, temp_dir: Path) -> None:
        """Test importing from a nonexistent file."""
        import_path = temp_dir / "nonexistent.json"
        result = manager.import_preset(import_path)

        assert result is None


class TestPresetManagerReset:
    """Test preset reset functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create a manager with temporary directory."""
        return PresetManager(presets_dir=temp_dir)

    def test_reset_to_defaults(self, manager: PresetManager, temp_dir: Path) -> None:
        """Test resetting to default presets."""
        # Save some user presets
        manager.save_preset(Preset(name="User1"))
        manager.save_preset(Preset(name="User2"))

        # Reset
        manager.reset_to_defaults()

        # User presets should be gone
        assert manager.load_preset("User1") is None
        assert manager.load_preset("User2") is None

        # Default presets should still work
        assert manager.load_preset("기본값") is not None
