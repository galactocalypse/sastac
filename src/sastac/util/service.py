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

    @staticmethod
    def get_workspace_files(
        path: Path,
        excluded_dirs: Iterable[str] = (".venv", "__pycache__"),
        excluded_types: Iterable[str] = (".pyc",),
        prefix: str = "",
    ) -> List[Path]:
        """
        Get workspace files, applying .gitignore rules and basic filtering.
        """
        from sastac.util.logger import logger
        import fnmatch
        
        CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".go", ".java", ".md", ".txt", ".json", ".yaml", ".yml"}
        
        ignore_patterns = []
        gitignore_path = path / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            ignore_patterns.append(line)
            except Exception as e:
                logger.warning(f"Failed to read .gitignore: {e}")

        ignore_cache = {}
        has_negations = any(p.startswith('!') for p in ignore_patterns)

        def is_ignored_by_gitignore(rel: Path) -> bool:
            if not ignore_patterns:
                return False
                
            parts = rel.parts
            ignored = False
            sub_str = ""
            
            for idx in range(len(parts)):
                part = parts[idx]
                if sub_str:
                    sub_str = f"{sub_str}/{part}"
                else:
                    sub_str = part
                    
                is_dir = (idx < len(parts) - 1)
                
                cache_key = (sub_str, is_dir)
                if cache_key in ignore_cache:
                    ignored = ignore_cache[cache_key]
                else:
                    component_ignored = ignored
                    
                    for pattern in ignore_patterns:
                        is_negation = pattern.startswith('!')
                        if is_negation:
                            patt = pattern[1:]
                        else:
                            patt = pattern
                            
                        must_be_dir = patt.endswith('/')
                        if must_be_dir:
                            patt = patt[:-1]
                        
                        if must_be_dir and not is_dir:
                            continue
                        
                        matched = False
                        if patt.startswith('/'):
                            matched = fnmatch.fnmatch(sub_str, patt[1:])
                        else:
                            matched = fnmatch.fnmatch(part, patt) or fnmatch.fnmatch(sub_str, patt)
                                
                        if matched:
                            component_ignored = not is_negation
                    
                    ignored = component_ignored
                    ignore_cache[cache_key] = ignored
                    
                if ignored and not has_negations:
                    return True
                        
            return ignored

        def filter_fn(p: Path) -> bool:
            # Get path relative to the root if it's absolute
            try:
                rel = p.relative_to(path)
            except ValueError:
                rel = p
                
            if is_ignored_by_gitignore(rel):
                return False
                
            exclude_dir = any(dir_name in p.parts for dir_name in excluded_dirs)
            exclude_type = any(p.suffix == ext for ext in excluded_types)
            is_code = p.suffix.lower() in CODE_EXTENSIONS
            prefix_match = (not prefix or str(rel).startswith(prefix))
            
            keep = not exclude_dir and not exclude_type and is_code and prefix_match
            return keep

        files = FileSystemService.list_files(path, filter_fn=filter_fn)
        logger.debug(f"Discovered {len(files)} files in {path} with prefix '{prefix}'")
        return files


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

