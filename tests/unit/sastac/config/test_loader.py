import yaml
from pathlib import Path
import importlib.resources as resources

from sastac.config.loader import ConfigService
from sastac.util.service import PackageDataService
import sastac.config.loader as loader



# ----------------------------
# Helpers
# ----------------------------

def write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data))


# ----------------------------
# Tests
# ----------------------------

def test_load_default_config_only(tmp_path, monkeypatch):
    import sastac.config.loader as loader

    fake_default = {
        "embeddings": {"model": "test-model", "vector_size": 111},
        "storage": {"qdrant_path": "/tmp/qdrant"},
    }

    monkeypatch.setattr(PackageDataService, "read_text", lambda pkg, name: (tmp_path / name).read_text())

    write_yaml(tmp_path / "default.yaml", fake_default)

    cfg = ConfigService.load()

    assert cfg.embeddings.model == "test-model"
    assert cfg.embeddings.vector_size == 111


def test_user_override(tmp_path, monkeypatch):
    """
    ~/.sastac/config.yaml should override defaults.
    """

    fake_default = {
        "embeddings": {"model": "default", "vector_size": 1024},
        "storage": {"qdrant_path": "/tmp/qdrant"},
    }

    monkeypatch.setattr(PackageDataService, "read_text", lambda pkg, name: (tmp_path / name).read_text())
    write_yaml(tmp_path / "default.yaml", fake_default)

    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    write_yaml(
        fake_home / ".sastac/config.yaml",
        {"embeddings": {"vector_size": 999}},
    )

    cfg = ConfigService.load()

    assert cfg.embeddings.model == "default"
    assert cfg.embeddings.vector_size == 999


def test_workspace_override(tmp_path, monkeypatch):
    """
    Workspace config should override user + default.
    """

    fake_default = {
        "embeddings": {"model": "default", "vector_size": 1024},
        "storage": {"qdrant_path": "/tmp/qdrant"},
    }

    monkeypatch.setattr(PackageDataService, "read_text", lambda pkg, name: (tmp_path / name).read_text())
    write_yaml(tmp_path / "default.yaml", fake_default)

    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    write_yaml(
        fake_home / ".sastac/config.yaml",
        {"embeddings": {"vector_size": 512}},
    )

    workspace = tmp_path / "workspace"
    write_yaml(
        workspace / ".sastac.yaml",
        {"embeddings": {"vector_size": 1024}},
    )

    cfg = ConfigService.load(workspace)

    assert cfg.embeddings.vector_size == 1024


def test_missing_files(tmp_path, monkeypatch):
    """
    Should not crash if no override files exist.
    """

    fake_default = {
        "embeddings": {"model": "default", "vector_size": 1024},
        "storage": {"qdrant_path": "/tmp/qdrant"},
    }

    monkeypatch.setattr(PackageDataService, "read_text", lambda pkg, name: (tmp_path / name).read_text())
    write_yaml(tmp_path / "default.yaml", fake_default)

    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    cfg = ConfigService.load(tmp_path / "workspace")

    assert cfg.embeddings.vector_size == 1024
