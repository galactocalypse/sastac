"""
Generic file system service.

Provides reusable utilities for listing and applying operations to files
under a given project root.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, List, Optional
from importlib.resources import files
import importlib.resources

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


class PackageDataService:
    """
    Retrieves internal data files bundled with the sastac package.
    """

    @staticmethod
    def read_text(package: str, filename: str) -> str:
        """
        Read the contents of a text file inside a given package.

        Args:
            package: The dot-separated package name (e.g., "sastac.files").
            filename: The name of the file to load (e.g., "chat_prompt.txt").

        Returns:
            The string content of the file.
            
        Raises:
            FileNotFoundError: If the resource does not exist in the package.
        """
        try:
            return files(package).joinpath(filename).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(f"Resource '{filename}' not found in package '{package}'")

    @staticmethod
    def read_bytes(package: str, filename: str) -> bytes:
        """
        Read the binary contents of a file inside a given package.
        """
        try:
            return files(package).joinpath(filename).read_bytes()
        except FileNotFoundError:
            raise FileNotFoundError(f"Resource '{filename}' not found in package '{package}'")


class FileService:
    """Service for basic file read/write operations."""

    @staticmethod
    def read_file(path: str | Path) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_file(path: str | Path, content: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

class InternalFileService:
    """Service for internal file operations, default to the <project root>/logs/ directory."""

    # Assuming service.py is at: <project_root>/src/sastac/util/service.py
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    LOGS_DIR = PROJECT_ROOT / "logs"

    @staticmethod
    def read_file(path: str | Path) -> str:
        return FileService.read_file(InternalFileService.LOGS_DIR / path)

    @staticmethod
    def write_file(path: str | Path, content: str) -> None:
        FileService.write_file(InternalFileService.LOGS_DIR / path, content)


class EnvService:
    """Service for loading and managing environment variables."""
    _loaded = False

    @staticmethod
    def load_env() -> None:
        if EnvService._loaded:
            return
            
        import os
        from dotenv import load_dotenv
        
        # Determine active environment (defaulting to 'local')
        sastac_env = os.environ.get("SASTAC_ENV", "local")
        
        # Load environment variables
        env_file = os.environ.get("SASTAC_ENV_FILE", f"env/{sastac_env}.env")
        env_path = Path(env_file)
        
        # Resolve relative to project root if it is not an absolute path
        if not env_path.is_absolute():
            env_path = InternalFileService.PROJECT_ROOT / env_path

        if env_path.exists():
            load_dotenv(env_path)
            
        EnvService._loaded = True

