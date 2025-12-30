"""Service for managing settings presets."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, ClassVar

from src.domain.types import Side, PlateType
from src.domain.value_objects.bridge_settings import BridgeSettings
from src.domain.value_objects.paper_size import PaperSize


@dataclass
class Preset:
    """A named preset containing processing settings."""

    name: str

    # Side and plate settings
    side: Side = Side.BACK
    plate_type: PlateType = PlateType.COPPER

    # Paper size
    paper_size_name: str = "국전"
    custom_width: float = 636.0
    custom_height: float = 939.0
    use_custom_size: bool = False

    # Bridge settings
    cut_gap: float = 3.0
    cut_interval: float = 60.0
    crease_gap: float = 2.0
    crease_interval: float = 50.0

    # Processing options
    apply_bridges: bool = True
    apply_straight_knife: bool = True
    remove_external: bool = True
    connect_segments: bool = False
    decompose_polylines: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert preset to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "side": self.side.name,
            "plate_type": self.plate_type.name,
            "paper_size_name": self.paper_size_name,
            "custom_width": self.custom_width,
            "custom_height": self.custom_height,
            "use_custom_size": self.use_custom_size,
            "cut_gap": self.cut_gap,
            "cut_interval": self.cut_interval,
            "crease_gap": self.crease_gap,
            "crease_interval": self.crease_interval,
            "apply_bridges": self.apply_bridges,
            "apply_straight_knife": self.apply_straight_knife,
            "remove_external": self.remove_external,
            "connect_segments": self.connect_segments,
            "decompose_polylines": self.decompose_polylines,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Preset:
        """Create preset from dictionary."""
        return cls(
            name=data.get("name", "Unnamed"),
            side=Side[data.get("side", "BACK")],
            plate_type=PlateType[data.get("plate_type", "COPPER")],
            paper_size_name=data.get("paper_size_name", "국전"),
            custom_width=data.get("custom_width", 636.0),
            custom_height=data.get("custom_height", 939.0),
            use_custom_size=data.get("use_custom_size", False),
            cut_gap=data.get("cut_gap", 3.0),
            cut_interval=data.get("cut_interval", 60.0),
            crease_gap=data.get("crease_gap", 2.0),
            crease_interval=data.get("crease_interval", 50.0),
            apply_bridges=data.get("apply_bridges", True),
            apply_straight_knife=data.get("apply_straight_knife", True),
            remove_external=data.get("remove_external", True),
            connect_segments=data.get("connect_segments", False),
            decompose_polylines=data.get("decompose_polylines", True),
        )

    def get_paper_size(self) -> PaperSize:
        """Get the paper size from this preset."""
        if self.use_custom_size:
            return PaperSize.custom(self.custom_width, self.custom_height)
        return PaperSize.from_standard(self.paper_size_name)

    def get_cut_bridge_settings(self) -> BridgeSettings:
        """Get cut bridge settings from this preset."""
        return BridgeSettings(
            gap_size=self.cut_gap,
            target_interval=self.cut_interval,
        )

    def get_crease_bridge_settings(self) -> BridgeSettings:
        """Get crease bridge settings from this preset."""
        return BridgeSettings(
            gap_size=self.crease_gap,
            target_interval=self.crease_interval,
        )


@dataclass
class PresetManager:
    """Manager for saving and loading presets."""

    presets_dir: Path = field(
        default_factory=lambda: Path.home() / ".diecut_automator" / "presets"
    )

    # Built-in default presets
    DEFAULT_PRESETS: ClassVar[list[Preset]] = [
        Preset(
            name="기본값",
            side=Side.BACK,
            plate_type=PlateType.COPPER,
            paper_size_name="국전",
        ),
        Preset(
            name="동판-앞면",
            side=Side.FRONT,
            plate_type=PlateType.COPPER,
            paper_size_name="국전",
        ),
        Preset(
            name="오토-뒷면",
            side=Side.BACK,
            plate_type=PlateType.AUTO,
            paper_size_name="국전",
        ),
        Preset(
            name="A3 크기",
            side=Side.BACK,
            plate_type=PlateType.COPPER,
            paper_size_name="A3",
        ),
    ]

    def __post_init__(self) -> None:
        """Ensure presets directory exists."""
        self.presets_dir.mkdir(parents=True, exist_ok=True)

    def get_preset_path(self, name: str) -> Path:
        """Get the file path for a preset."""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return self.presets_dir / f"{safe_name}.json"

    def save_preset(self, preset: Preset) -> None:
        """
        Save a preset to disk.

        Args:
            preset: The preset to save
        """
        path = self.get_preset_path(preset.name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(preset.to_dict(), f, ensure_ascii=False, indent=2)

    def load_preset(self, name: str) -> Preset | None:
        """
        Load a preset from disk.

        Args:
            name: Name of the preset to load

        Returns:
            The loaded preset or None if not found
        """
        path = self.get_preset_path(name)
        if not path.exists():
            # Check default presets
            for default in self.DEFAULT_PRESETS:
                if default.name == name:
                    return default
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Preset.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset from disk.

        Args:
            name: Name of the preset to delete

        Returns:
            True if deleted, False if not found
        """
        path = self.get_preset_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_presets(self) -> list[str]:
        """
        List all available preset names.

        Returns:
            List of preset names (defaults + user presets)
        """
        names = [p.name for p in self.DEFAULT_PRESETS]

        # Add user presets from disk
        if self.presets_dir.exists():
            for path in self.presets_dir.glob("*.json"):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    name = data.get("name")
                    if name and name not in names:
                        names.append(name)
                except (json.JSONDecodeError, KeyError):
                    continue

        return sorted(names)

    def get_default_preset(self) -> Preset:
        """Get the default preset."""
        return self.DEFAULT_PRESETS[0]

    def export_preset(self, name: str, export_path: Path) -> bool:
        """
        Export a preset to a file.

        Args:
            name: Name of the preset to export
            export_path: Path to export to

        Returns:
            True if exported successfully
        """
        preset = self.load_preset(name)
        if preset is None:
            return False

        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(preset.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def import_preset(self, import_path: Path) -> Preset | None:
        """
        Import a preset from a file.

        Args:
            import_path: Path to import from

        Returns:
            The imported preset or None on failure
        """
        if not import_path.exists():
            return None

        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            preset = Preset.from_dict(data)
            self.save_preset(preset)
            return preset
        except (json.JSONDecodeError, KeyError):
            return None

    def reset_to_defaults(self) -> None:
        """Reset all presets by removing user presets."""
        if self.presets_dir.exists():
            for path in self.presets_dir.glob("*.json"):
                path.unlink()
