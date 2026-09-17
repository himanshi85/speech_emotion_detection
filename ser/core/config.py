"""Load and validate experiment YAML configs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from ser.core.paths import PROJECT_ROOT, model_output_dir

CONFIGS_DIR = PROJECT_ROOT / "configs"


def load_yaml(path: Path | str) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def config_path_for_model(model_key: str) -> Path:
    mapping = {
        "emotion2vec_plus": "emotion2vec_plus.yaml",
    }
    filename = mapping.get(model_key, f"{model_key}.yaml")
    path = CONFIGS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"No config for model '{model_key}': {path}")
    return path


def load_model_config(model_key: str, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    base_path = CONFIGS_DIR / "_base.yaml"
    base = load_yaml(base_path) if base_path.exists() else {}
    cfg = {**base, **load_yaml(config_path_for_model(model_key))}
    cfg.setdefault("model_key", model_key)
    if "output_dir" not in cfg:
        cfg["output_dir"] = str(model_output_dir(model_key))
    if overrides:
        cfg.update(overrides)
    out = Path(cfg["output_dir"])
    if not out.is_absolute():
        cfg["output_dir"] = str((PROJECT_ROOT / out).resolve())
    data_dir = cfg.get("data_dir")
    if data_dir and not Path(data_dir).is_absolute():
        cfg["data_dir"] = str((PROJECT_ROOT / data_dir).resolve())
    return cfg


def save_config(cfg: Dict[str, Any], path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    return path
