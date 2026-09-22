"""
Experiment configuration helpers (YAML + CLI-aligned defaults).

Section 10 introduces freeze_encoder; later sections extend this config.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from xlsr.constants import MODEL_NAME, SAMPLE_RATE
from xlsr.labels import NUM_CLASSES
from xlsr.model import DEFAULT_DROPOUT
from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR


def default_config(freeze_encoder: bool = False) -> Dict[str, Any]:
    """Default experiment config. Full fine-tuning unless freeze_encoder=True."""
    return {
        "model_name": MODEL_NAME,
        "num_classes": NUM_CLASSES,
        "sample_rate": SAMPLE_RATE,
        "dropout": DEFAULT_DROPOUT,
        "freeze_encoder": bool(freeze_encoder),
        "fine_tuning_mode": "frozen_encoder" if freeze_encoder else "full",
        "data_dir": str(DEFAULT_DATA_DIR),
        "output_dir": str(DEFAULT_OUTPUT_DIR),
        # Placeholders filled in later sections (optimizer, training, etc.)
        "batch_size": 4,
        "num_epochs": 20,
        "encoder_learning_rate": 1.0e-5,
        "classifier_learning_rate": 1.0e-4,
        "weight_decay": 0.01,
        "warmup_ratio": 0.1,
        "gradient_accumulation_steps": 4,
        "mixed_precision": True,
        "early_stopping_patience": 5,
        "seed": 42,
    }


def save_config(config: Dict[str, Any], path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False)
    return path


def load_config(path: Path | str) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def write_default_experiment_config(
    output_dir: Optional[Path | str] = None,
    freeze_encoder: bool = False,
) -> Path:
    from xlsr.experiment_dirs import create_experiment_dirs

    exp = create_experiment_dirs(output_dir or DEFAULT_OUTPUT_DIR)
    cfg = default_config(freeze_encoder=freeze_encoder)
    return save_config(cfg, exp["config"])
