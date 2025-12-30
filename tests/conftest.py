"""
Pytest configuration and fixtures for DieCut Automator tests.
"""
import pytest
from pathlib import Path


@pytest.fixture
def fixtures_path() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_dxf_path(fixtures_path: Path) -> Path:
    """Return the path to the sample DXF file."""
    return fixtures_path / "sample.dxf"
