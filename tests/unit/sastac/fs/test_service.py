"""
Unit tests for FileSystemService.
"""

from pathlib import Path
from typing import List

import pytest

from sastac.util.service import FileSystemService


class TestFileSystemService:
    def _create_file(self, path: Path, content: str = "") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_list_files_recursive(self, tmp_path: Path) -> None:
        self._create_file(tmp_path / "a.py")
        self._create_file(tmp_path / "b.txt")
        self._create_file(tmp_path / "sub" / "c.py")

        files = FileSystemService.list_files(tmp_path, recursive=True)

        assert len(files) == 3
        assert files == sorted(files)

    def test_list_files_non_recursive(self, tmp_path: Path) -> None:
        self._create_file(tmp_path / "a.py")
        self._create_file(tmp_path / "sub" / "b.py")

        files = FileSystemService.list_files(tmp_path, recursive=False)

        assert len(files) == 1
        assert files[0].name == "a.py"

    def test_list_files_with_filter(self, tmp_path: Path) -> None:
        self._create_file(tmp_path / "a.py")
        self._create_file(tmp_path / "b.txt")

        files = FileSystemService.list_files(
            tmp_path,
            recursive=True,
            filter_fn=lambda p: p.suffix == ".py",
        )

        assert len(files) == 1
        assert files[0].suffix == ".py"

    def test_list_files_by_extension(self, tmp_path: Path) -> None:
        self._create_file(tmp_path / "a.py")
        self._create_file(tmp_path / "b.PY")
        self._create_file(tmp_path / "c.txt")

        files = FileSystemService.list_files_by_extension(
            tmp_path,
            extensions=[".py"],
        )

        assert len(files) == 2

    def test_apply_function_recursive(self, tmp_path: Path) -> None:
        self._create_file(tmp_path / "a.py")
        self._create_file(tmp_path / "sub" / "b.py")

        collected: List[str] = []

        def collector(path: Path) -> None:
            collected.append(path.name)

        FileSystemService.apply(
            root=tmp_path,
            func=collector,
            recursive=True,
        )

        assert sorted(collected) == ["a.py", "b.py"]

    def test_apply_with_filter(self, tmp_path: Path) -> None:
        self._create_file(tmp_path / "a.py")
        self._create_file(tmp_path / "b.txt")

        collected: List[str] = []

        FileSystemService.apply(
            root=tmp_path,
            func=lambda p: collected.append(p.name),
            filter_fn=lambda p: p.suffix == ".py",
        )

        assert collected == ["a.py"]

    def test_root_not_exists(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"

        with pytest.raises(FileNotFoundError):
            FileSystemService.list_files(missing)

    def test_root_not_directory(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file.txt"
        file_path.write_text("data")

        with pytest.raises(NotADirectoryError):
            FileSystemService.list_files(file_path)
