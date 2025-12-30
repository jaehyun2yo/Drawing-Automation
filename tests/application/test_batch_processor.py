"""Tests for BatchProcessor service."""
from __future__ import annotations

from pathlib import Path
import tempfile
import pytest
from typing import Any

from src.application.services.batch_processor import (
    BatchProcessor,
    BatchProcessorOptions,
    BatchResult,
    BatchItemResult,
    BatchItemStatus,
)


class TestBatchItemResult:
    """Test BatchItemResult data class."""

    def test_create_result(self) -> None:
        """Test creating a batch item result."""
        result = BatchItemResult(input_path=Path("test.dxf"))

        assert result.input_path == Path("test.dxf")
        assert result.output_path is None
        assert result.status == BatchItemStatus.PENDING
        assert result.error_message is None

    def test_is_success(self) -> None:
        """Test is_success property."""
        result = BatchItemResult(
            input_path=Path("test.dxf"),
            status=BatchItemStatus.COMPLETED
        )

        assert result.is_success is True

    def test_is_failed(self) -> None:
        """Test is_failed property."""
        result = BatchItemResult(
            input_path=Path("test.dxf"),
            status=BatchItemStatus.FAILED,
            error_message="Some error"
        )

        assert result.is_failed is True


class TestBatchResult:
    """Test BatchResult data class."""

    def test_empty_result(self) -> None:
        """Test empty batch result."""
        result = BatchResult()

        assert result.total_count == 0
        assert result.completed_count == 0
        assert result.failed_count == 0
        assert result.success_rate == 0.0

    def test_completed_count(self) -> None:
        """Test counting completed items."""
        result = BatchResult(items=[
            BatchItemResult(Path("a.dxf"), status=BatchItemStatus.COMPLETED),
            BatchItemResult(Path("b.dxf"), status=BatchItemStatus.COMPLETED),
            BatchItemResult(Path("c.dxf"), status=BatchItemStatus.FAILED),
        ])

        assert result.completed_count == 2
        assert result.failed_count == 1
        assert result.total_count == 3

    def test_success_rate(self) -> None:
        """Test success rate calculation."""
        result = BatchResult(items=[
            BatchItemResult(Path("a.dxf"), status=BatchItemStatus.COMPLETED),
            BatchItemResult(Path("b.dxf"), status=BatchItemStatus.COMPLETED),
            BatchItemResult(Path("c.dxf"), status=BatchItemStatus.FAILED),
            BatchItemResult(Path("d.dxf"), status=BatchItemStatus.SKIPPED),
        ])

        assert result.success_rate == 50.0  # 2 out of 4

    def test_get_failed_items(self) -> None:
        """Test getting list of failed items."""
        failed_item = BatchItemResult(Path("fail.dxf"), status=BatchItemStatus.FAILED)
        result = BatchResult(items=[
            BatchItemResult(Path("ok.dxf"), status=BatchItemStatus.COMPLETED),
            failed_item,
        ])

        failed = result.get_failed_items()

        assert len(failed) == 1
        assert failed[0] is failed_item


class TestBatchProcessor:
    """Test BatchProcessor service."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def sample_dxf_files(self, temp_dir: Path) -> list[Path]:
        """Create sample DXF files for testing."""
        files = []
        for i in range(3):
            file_path = temp_dir / f"test_{i}.dxf"
            file_path.write_text(f"DXF content {i}")
            files.append(file_path)
        return files

    @pytest.fixture
    def mock_processor(self):
        """Create a mock file processor."""
        def processor(input_path: Path, output_path: Path, **options: Any) -> dict[str, Any]:
            # Copy content to output
            content = input_path.read_text()
            output_path.write_text(f"Processed: {content}")
            return {"lines_processed": 10}
        return processor

    def test_process_empty_list(self, mock_processor) -> None:
        """Test processing empty file list."""
        processor = BatchProcessor()

        result = processor.process([], mock_processor)

        assert result.total_count == 0
        assert result.cancelled is False

    def test_process_single_file(
        self, temp_dir: Path, sample_dxf_files: list[Path], mock_processor
    ) -> None:
        """Test processing a single file."""
        processor = BatchProcessor()

        result = processor.process([sample_dxf_files[0]], mock_processor)

        assert result.total_count == 1
        assert result.completed_count == 1
        assert result.items[0].is_success

    def test_process_multiple_files(
        self, temp_dir: Path, sample_dxf_files: list[Path], mock_processor
    ) -> None:
        """Test processing multiple files."""
        processor = BatchProcessor()

        result = processor.process(sample_dxf_files, mock_processor)

        assert result.total_count == 3
        assert result.completed_count == 3
        assert result.success_rate == 100.0

    def test_output_suffix(
        self, temp_dir: Path, sample_dxf_files: list[Path], mock_processor
    ) -> None:
        """Test output file naming with suffix."""
        processor = BatchProcessor(
            options=BatchProcessorOptions(output_suffix="_output")
        )

        result = processor.process([sample_dxf_files[0]], mock_processor)

        assert result.items[0].output_path is not None
        assert "_output.dxf" in str(result.items[0].output_path)

    def test_custom_output_directory(
        self, temp_dir: Path, sample_dxf_files: list[Path], mock_processor
    ) -> None:
        """Test output to custom directory."""
        output_dir = temp_dir / "output"
        processor = BatchProcessor(
            options=BatchProcessorOptions(output_directory=output_dir)
        )

        result = processor.process([sample_dxf_files[0]], mock_processor)

        assert result.items[0].output_path is not None
        assert result.items[0].output_path.parent == output_dir
        assert output_dir.exists()

    def test_file_not_found(self, mock_processor) -> None:
        """Test handling of non-existent file."""
        processor = BatchProcessor()
        files = [Path("nonexistent.dxf")]

        result = processor.process(files, mock_processor)

        assert result.total_count == 1
        assert result.failed_count == 1
        assert "not found" in result.items[0].error_message.lower()

    def test_skip_non_dxf_files(self, temp_dir: Path, mock_processor) -> None:
        """Test skipping non-DXF files."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("Not a DXF")
        processor = BatchProcessor(
            options=BatchProcessorOptions(skip_invalid_files=True)
        )

        result = processor.process([txt_file], mock_processor)

        assert result.total_count == 1
        assert result.skipped_count == 1
        assert result.items[0].status == BatchItemStatus.SKIPPED

    def test_fail_on_non_dxf_files(self, temp_dir: Path, mock_processor) -> None:
        """Test failing on non-DXF files when skip is disabled."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("Not a DXF")
        processor = BatchProcessor(
            options=BatchProcessorOptions(skip_invalid_files=False)
        )

        result = processor.process([txt_file], mock_processor)

        assert result.total_count == 1
        assert result.failed_count == 1

    def test_skip_existing_output(
        self, temp_dir: Path, sample_dxf_files: list[Path], mock_processor
    ) -> None:
        """Test skipping when output file already exists."""
        processor = BatchProcessor(
            options=BatchProcessorOptions(overwrite_existing=False)
        )
        # Create existing output file
        output_path = temp_dir / "test_0_processed.dxf"
        output_path.write_text("Existing")

        result = processor.process([sample_dxf_files[0]], mock_processor)

        assert result.skipped_count == 1
        assert "already exists" in result.items[0].error_message.lower()

    def test_overwrite_existing(
        self, temp_dir: Path, sample_dxf_files: list[Path], mock_processor
    ) -> None:
        """Test overwriting existing output file."""
        processor = BatchProcessor(
            options=BatchProcessorOptions(overwrite_existing=True)
        )
        # Create existing output file
        output_path = temp_dir / "test_0_processed.dxf"
        output_path.write_text("Existing")

        result = processor.process([sample_dxf_files[0]], mock_processor)

        assert result.completed_count == 1
        assert output_path.read_text().startswith("Processed:")

    def test_stop_on_error(
        self, temp_dir: Path, sample_dxf_files: list[Path]
    ) -> None:
        """Test stopping on first error."""
        def failing_processor(input_path: Path, output_path: Path, **options):
            if "test_1" in str(input_path):
                raise ValueError("Processing failed")
            output_path.write_text("OK")
            return {}

        processor = BatchProcessor(
            options=BatchProcessorOptions(stop_on_error=True)
        )

        result = processor.process(sample_dxf_files, failing_processor)

        assert result.cancelled is True
        assert result.completed_count == 1  # First file
        assert result.failed_count == 1  # Second file
        assert result.skipped_count == 1  # Third file skipped

    def test_continue_on_error(
        self, temp_dir: Path, sample_dxf_files: list[Path]
    ) -> None:
        """Test continuing after error."""
        def failing_processor(input_path: Path, output_path: Path, **options):
            if "test_1" in str(input_path):
                raise ValueError("Processing failed")
            output_path.write_text("OK")
            return {}

        processor = BatchProcessor(
            options=BatchProcessorOptions(stop_on_error=False)
        )

        result = processor.process(sample_dxf_files, failing_processor)

        assert result.cancelled is False
        assert result.completed_count == 2  # First and third files
        assert result.failed_count == 1  # Second file failed

    def test_cancel_processing(
        self, temp_dir: Path, sample_dxf_files: list[Path]
    ) -> None:
        """Test cancelling batch processing."""
        call_count = 0

        def counting_processor(input_path: Path, output_path: Path, **options):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                processor.cancel()
            output_path.write_text("OK")
            return {}

        processor = BatchProcessor()

        result = processor.process(sample_dxf_files, counting_processor)

        # First two files processed, third skipped due to cancel
        assert result.cancelled is True
        assert result.completed_count == 2
        assert result.skipped_count == 1

    def test_progress_callback(
        self, temp_dir: Path, sample_dxf_files: list[Path], mock_processor
    ) -> None:
        """Test progress callback is called."""
        progress_calls = []

        def progress_callback(current: int, total: int, filename: str):
            progress_calls.append((current, total, filename))

        processor = BatchProcessor()
        processor.process(sample_dxf_files, mock_processor, progress_callback)

        # Should have 4 calls: 0/3, 1/3, 2/3, and 3/3 (complete)
        assert len(progress_calls) == 4
        assert progress_calls[0][0] == 0
        assert progress_calls[-1] == (3, 3, "Complete")

    def test_statistics_collected(
        self, temp_dir: Path, sample_dxf_files: list[Path], mock_processor
    ) -> None:
        """Test that statistics are collected from processor."""
        processor = BatchProcessor()

        result = processor.process([sample_dxf_files[0]], mock_processor)

        assert result.items[0].statistics.get("lines_processed") == 10


class TestBatchProcessorValidation:
    """Test file validation methods."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    def test_validate_files(self, temp_dir: Path) -> None:
        """Test validating file list."""
        dxf_file = temp_dir / "valid.dxf"
        dxf_file.write_text("DXF")
        txt_file = temp_dir / "invalid.txt"
        txt_file.write_text("TXT")
        missing_file = temp_dir / "missing.dxf"

        processor = BatchProcessor()
        valid, invalid = processor.validate_files([dxf_file, txt_file, missing_file])

        assert len(valid) == 1
        assert valid[0] == dxf_file
        assert len(invalid) == 2

    def test_estimate_output_size(self, temp_dir: Path) -> None:
        """Test estimating output size."""
        files = []
        for i in range(3):
            f = temp_dir / f"test_{i}.dxf"
            f.write_text("X" * 100)  # 100 bytes each
            files.append(f)

        processor = BatchProcessor()
        size = processor.estimate_output_size(files)

        assert size == 300  # 3 files * 100 bytes
