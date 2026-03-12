import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from sastac.util.service import FileService

def test_write_and_read_file(tmp_path):
    # Setup paths
    test_file_path = tmp_path / "subdir" / "test_file.txt"
    test_content = "This is a test file.\nIt contains multiple lines.\nUTF-8 chars: 🎉🔥©"

    # Test writing
    FileService.write_file(test_file_path, test_content)
    
    # Verify file was actually created in the filesystem
    assert test_file_path.exists()
    assert test_file_path.read_text(encoding="utf-8") == test_content

    # Test reading via the service
    read_content = FileService.read_file(test_file_path)
    assert read_content == test_content

def test_write_file_creates_parent_directories(tmp_path):
    # Deeply nested path
    deep_path = tmp_path / "a" / "b" / "c" / "deep.txt"
    test_content = "deeply nested"

    FileService.write_file(deep_path, test_content)

    assert deep_path.exists()
    assert FileService.read_file(deep_path) == test_content

def test_read_file_not_found(tmp_path):
    missing_path = tmp_path / "does_not_exist.txt"
    
    with pytest.raises(FileNotFoundError):
        FileService.read_file(missing_path)

def test_internal_file_service(tmp_path, monkeypatch):
    from sastac.util.service import InternalFileService

    monkeypatch.setattr(InternalFileService, "LOGS_DIR", tmp_path / "logs")
    
    test_content = "internal test content"
    InternalFileService.write_file("test.log", test_content)

    log_path = tmp_path / "logs" / "test.log"
    assert log_path.exists()
    assert log_path.read_text(encoding="utf-8") == test_content
    assert InternalFileService.read_file("test.log") == test_content
