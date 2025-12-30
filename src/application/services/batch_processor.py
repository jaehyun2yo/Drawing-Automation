"""Batch processing service for multiple DXF files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol
from enum import Enum, auto


class BatchItemStatus(Enum):
    """Status of a single batch item."""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class BatchItemResult:
    """Result for a single file in batch processing."""

    input_path: Path
    output_path: Path | None = None
    status: BatchItemStatus = BatchItemStatus.PENDING
    error_message: str | None = None
    statistics: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if processing was successful."""
        return self.status == BatchItemStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if processing failed."""
        return self.status == BatchItemStatus.FAILED


@dataclass
class BatchResult:
    """Result of batch processing operation."""

    items: list[BatchItemResult] = field(default_factory=list)
    cancelled: bool = False

    @property
    def total_count(self) -> int:
        """Get total number of items."""
        return len(self.items)

    @property
    def completed_count(self) -> int:
        """Get number of successfully processed items."""
        return sum(1 for item in self.items if item.is_success)

    @property
    def failed_count(self) -> int:
        """Get number of failed items."""
        return sum(1 for item in self.items if item.is_failed)

    @property
    def skipped_count(self) -> int:
        """Get number of skipped items."""
        return sum(1 for item in self.items if item.status == BatchItemStatus.SKIPPED)

    @property
    def success_rate(self) -> float:
        """Get success rate as a percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.completed_count / self.total_count) * 100

    def get_failed_items(self) -> list[BatchItemResult]:
        """Get list of failed items."""
        return [item for item in self.items if item.is_failed]

    def get_completed_items(self) -> list[BatchItemResult]:
        """Get list of completed items."""
        return [item for item in self.items if item.is_success]


class FileProcessor(Protocol):
    """Protocol for file processing function."""

    def __call__(
        self,
        input_path: Path,
        output_path: Path,
        **options: Any
    ) -> dict[str, Any]:
        """Process a single file.

        Returns:
            Statistics dictionary from processing
        """
        ...


@dataclass
class BatchProcessorOptions:
    """Options for batch processing."""

    output_directory: Path | None = None
    output_suffix: str = "_processed"
    overwrite_existing: bool = False
    stop_on_error: bool = False
    skip_invalid_files: bool = True


@dataclass
class BatchProcessor:
    """Service for processing multiple DXF files in batch."""

    options: BatchProcessorOptions = field(default_factory=BatchProcessorOptions)
    _cancel_requested: bool = field(default=False, init=False)

    def process(
        self,
        input_files: list[Path],
        processor: FileProcessor,
        progress_callback: Callable[[int, int, str], None] | None = None,
        **processor_options: Any
    ) -> BatchResult:
        """
        Process multiple files in batch.

        Args:
            input_files: List of input file paths
            processor: Function to process each file
            progress_callback: Optional callback(current, total, filename)
            **processor_options: Options passed to the processor function

        Returns:
            BatchResult with processing results
        """
        self._cancel_requested = False
        result = BatchResult()

        total = len(input_files)

        for index, input_path in enumerate(input_files):
            if self._cancel_requested:
                result.cancelled = True
                # Mark remaining as skipped
                for remaining in input_files[index:]:
                    result.items.append(BatchItemResult(
                        input_path=remaining,
                        status=BatchItemStatus.SKIPPED,
                        error_message="Cancelled by user"
                    ))
                break

            # Report progress
            if progress_callback:
                progress_callback(index, total, input_path.name)

            # Process the file
            item_result = self._process_single_file(
                input_path, processor, **processor_options
            )
            result.items.append(item_result)

            # Stop on error if requested
            if item_result.is_failed and self.options.stop_on_error:
                result.cancelled = True
                # Mark remaining as skipped
                for remaining in input_files[index + 1:]:
                    result.items.append(BatchItemResult(
                        input_path=remaining,
                        status=BatchItemStatus.SKIPPED,
                        error_message="Stopped due to previous error"
                    ))
                break

        # Final progress callback
        if progress_callback:
            progress_callback(total, total, "Complete")

        return result

    def cancel(self) -> None:
        """Request cancellation of batch processing."""
        self._cancel_requested = True

    def _process_single_file(
        self,
        input_path: Path,
        processor: FileProcessor,
        **options: Any
    ) -> BatchItemResult:
        """
        Process a single file.

        Args:
            input_path: Input file path
            processor: Processing function
            **options: Processor options

        Returns:
            BatchItemResult for this file
        """
        item_result = BatchItemResult(
            input_path=input_path,
            status=BatchItemStatus.PROCESSING
        )

        # Validate input file
        if not input_path.exists():
            item_result.status = BatchItemStatus.FAILED
            item_result.error_message = f"File not found: {input_path}"
            return item_result

        if not input_path.suffix.lower() == '.dxf':
            if self.options.skip_invalid_files:
                item_result.status = BatchItemStatus.SKIPPED
                item_result.error_message = "Not a DXF file"
                return item_result
            else:
                item_result.status = BatchItemStatus.FAILED
                item_result.error_message = "Not a DXF file"
                return item_result

        # Determine output path
        output_path = self._get_output_path(input_path)
        item_result.output_path = output_path

        # Check if output exists
        if output_path.exists() and not self.options.overwrite_existing:
            item_result.status = BatchItemStatus.SKIPPED
            item_result.error_message = "Output file already exists"
            return item_result

        # Process the file
        try:
            statistics = processor(input_path, output_path, **options)
            item_result.status = BatchItemStatus.COMPLETED
            item_result.statistics = statistics or {}
        except Exception as e:
            item_result.status = BatchItemStatus.FAILED
            item_result.error_message = str(e)

        return item_result

    def _get_output_path(self, input_path: Path) -> Path:
        """
        Get output path for an input file.

        Args:
            input_path: Input file path

        Returns:
            Output file path
        """
        # Determine output directory
        if self.options.output_directory:
            output_dir = self.options.output_directory
            # Create directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = input_path.parent

        # Create output filename
        stem = input_path.stem
        suffix = input_path.suffix
        output_name = f"{stem}{self.options.output_suffix}{suffix}"

        return output_dir / output_name

    def validate_files(self, files: list[Path]) -> tuple[list[Path], list[Path]]:
        """
        Validate list of files for batch processing.

        Args:
            files: List of file paths to validate

        Returns:
            Tuple of (valid_files, invalid_files)
        """
        valid = []
        invalid = []

        for file_path in files:
            if not file_path.exists():
                invalid.append(file_path)
            elif not file_path.suffix.lower() == '.dxf':
                invalid.append(file_path)
            else:
                valid.append(file_path)

        return valid, invalid

    def estimate_output_size(self, input_files: list[Path]) -> int:
        """
        Estimate total output size based on input files.

        Args:
            input_files: List of input file paths

        Returns:
            Estimated total size in bytes
        """
        total_size = 0
        for file_path in input_files:
            if file_path.exists():
                # Output is typically similar size to input for DXF
                total_size += file_path.stat().st_size

        return total_size
