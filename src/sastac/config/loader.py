# src/sastac/config/loader.py

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Optional
from sastac.util.service import PackageDataService, EnvService
import os

from sastac.config.schema import SastacConfig, EmbeddingConfig, LLMConfig


# -------------------------------------------------------
# ConfigService
# -------------------------------------------------------

class ConfigService:
    """
    Loads and merges sastac configuration from multiple sources:

    1. Built-in defaults  (``sastac/files/config/default.yaml``)
    2. User overrides     (``~/.sastac/config.yaml``)
    3. Workspace overrides(``<workspace>/.sastac.yaml``)

    Usage
    -----
    cfg = ConfigService.load()                     # defaults + user overrides
    cfg = ConfigService.load(workspace_root=path)  # + workspace overrides
    """

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    @staticmethod
    def load(workspace_root: Optional[Path] = None) -> SastacConfig:
        """Load and merge config from all sources, returning a SastacConfig."""
        cfg = ConfigService._load_defaults()
        cfg = ConfigService._deep_merge(cfg, ConfigService._read_yaml(Path.home() / ".sastac/config.yaml"))
        if workspace_root:
            cfg = ConfigService._deep_merge(cfg, ConfigService._read_yaml(workspace_root / ".sastac.yaml"))
        return ConfigService._build_config(cfg)

    @staticmethod
    def load_defaults() -> dict:
        """Return the raw default config dict (no user/workspace overrides)."""
        return ConfigService._load_defaults()

    # --------------------------------------------------
    # Private helpers
    # --------------------------------------------------

    @staticmethod
    def _load_defaults() -> dict:
        EnvService.load_env()
        # Read the explicit config file requested by the environment without any default fallback
        config_file = os.environ["SASTAC_CONFIG_FILE"]
        data = PackageDataService.read_text("sastac.files.config", config_file)
        return yaml.safe_load(data) or {}

    @staticmethod
    def _read_yaml(path: Path) -> dict:
        if path.exists():
            return yaml.safe_load(path.read_text()) or {}
        return {}

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        result = dict(base)
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(result.get(k), dict):
                result[k] = ConfigService._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    @staticmethod
    def _build_config(cfg: dict) -> SastacConfig:
        task_refiner_cfg = cfg.get("task_refiner")
        task_planner_cfg = cfg.get("task_planner")
        return SastacConfig(
            embeddings=EmbeddingConfig(**cfg["embeddings"]),
            task_refiner=LLMConfig(**task_refiner_cfg) if task_refiner_cfg else None,
            task_planner=LLMConfig(**task_planner_cfg) if task_planner_cfg else None,
        )



