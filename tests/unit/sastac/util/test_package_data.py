import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from sastac.util.service import PackageDataService
import importlib.resources as resources

def test_read_text(tmp_path, monkeypatch):
    test_content = "hello world"
    (tmp_path / "test.txt").write_text(test_content, encoding="utf-8")

    # Mock importlib.resources.files
    monkeypatch.setattr("sastac.util.service.files", lambda pkg: tmp_path)

    text = PackageDataService.read_text("dummy.package", "test.txt")
    assert text == test_content

def test_read_bytes(tmp_path, monkeypatch):
    test_content = b"\x00\x01\x02"
    (tmp_path / "test.bin").write_bytes(test_content)

    monkeypatch.setattr("sastac.util.service.files", lambda pkg: tmp_path)

    data = PackageDataService.read_bytes("dummy.package", "test.bin")
    assert data == test_content

def test_read_text_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("sastac.util.service.files", lambda pkg: tmp_path)

    with pytest.raises(FileNotFoundError, match="not found in package"):
        PackageDataService.read_text("dummy.package", "missing.txt")

def test_read_bytes_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("sastac.util.service.files", lambda pkg: tmp_path)

    with pytest.raises(FileNotFoundError, match="not found in package"):
        PackageDataService.read_bytes("dummy.package", "missing.bin")
