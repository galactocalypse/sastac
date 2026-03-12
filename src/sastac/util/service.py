"""
Generic file system service.

Provides reusable utilities for listing and applying operations to files
under a given project root.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, List, Optional


FilePredicate = Callable[[Path], bool]
FileCallback = Callable[[Path], None]


class FileSystemService:
    """
    Stateless file management service.

    Why:
        Centralizes filesystem traversal logic to avoid duplication and
        inconsistent behavior across modules.
    """

    @staticmethod
    def list_files(
        root: Path,
        recursive: bool = True,
        filter_fn: Optional[FilePredicate] = None,
    ) -> List[Path]:
        """
        List files under root.

        Args:
            root: Root directory.
            recursive: Whether to traverse subdirectories.
            filter_fn: Optional predicate to filter files.

        Returns:
            Sorted list of file paths.
        """
        if not root.exists():
            raise FileNotFoundError(f"Root path does not exist: {root}")

        if not root.is_dir():
            raise NotADirectoryError(f"Root path is not a directory: {root}")

        pattern = "**/*" if recursive else "*"
        paths = (p for p in root.glob(pattern) if p.is_file())

        if filter_fn:
            paths = (p for p in paths if filter_fn(p))

        return sorted(paths)

    @staticmethod
    def apply(
        root: Path,
        func: FileCallback,
        recursive: bool = True,
        filter_fn: Optional[FilePredicate] = None,
    ) -> None:
        """
        Apply function to files under root.

        Args:
            root: Root directory.
            func: Function to apply to each file.
            recursive: Whether to traverse subdirectories.
            filter_fn: Optional predicate to filter files.
        """
        files = FileSystemService.list_files(
            root=root,
            recursive=recursive,
            filter_fn=filter_fn,
        )

        for file_path in files:
            func(file_path)

    @staticmethod
    def list_files_by_extension(
        root: Path,
        extensions: Iterable[str],
        recursive: bool = True,
    ) -> List[Path]:
        """
        List files matching given extensions.

        Args:
            root: Root directory.
            extensions: Iterable of extensions (e.g. ['.py', '.js']).
            recursive: Whether to traverse subdirectories.

        Returns:
            Sorted list of matching files.
        """
        normalized = {ext.lower() for ext in extensions}

        return FileSystemService.list_files(
            root=root,
            recursive=recursive,
            filter_fn=lambda p: p.suffix.lower() in normalized,
        )
