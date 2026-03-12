# src/sastac/config/loader.py

import yaml
from pathlib import Path
from importlib.resources import files
from sastac.config.schema import SastacConfig
from sastac.config.schema import (
    SastacConfig,
    EmbeddingConfig,
    LLMConfig
)


def _read_yaml(path: Path):
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)

    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v

    return result


def load_default_config() -> dict:
    data = files("sastac.files.config").joinpath("default.yaml").read_text()
    return yaml.safe_load(data) or {}


def load_config(workspace_root=None):
    cfg = load_default_config()

    cfg = deep_merge(cfg, _read_yaml(Path.home() / ".sastac/config.yaml"))

    if workspace_root:
        cfg = deep_merge(cfg, _read_yaml(workspace_root / ".sastac.yaml"))

    task_refiner_cfg = cfg.get("task_refiner")
    task_planner_cfg = cfg.get("task_planner")

    return SastacConfig(
        embeddings=EmbeddingConfig(**cfg["embeddings"]),
        task_refiner=LLMConfig(**task_refiner_cfg) if task_refiner_cfg else None,
        task_planner=LLMConfig(**task_planner_cfg) if task_planner_cfg else None,
    )
