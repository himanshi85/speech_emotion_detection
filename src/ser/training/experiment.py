"""Experiment directory setup."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

from ser.core.paths import OUTPUT_SUBDIRS

logger = logging.getLogger(__name__)


def create_experiment_dirs(output_dir: Path | str) -> Dict[str, Path]:
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Path] = {"root": root}
    for rel in OUTPUT_SUBDIRS:
        p = root / rel
        p.mkdir(parents=True, exist_ok=True)
        paths[rel.replace("/", "_")] = p
    paths["checkpoints"] = root / "checkpoints"
    paths["best_model"] = root / "checkpoints" / "best_model"
    paths["final_model"] = root / "checkpoints" / "final_model"
    paths["metrics"] = root / "metrics"
    paths["predictions_train"] = root / "predictions" / "train"
    paths["predictions_validation"] = root / "predictions" / "validation"
    paths["predictions_test"] = root / "predictions" / "test"
    paths["logs"] = root / "logs"
    paths["config"] = root / "config.yaml"
    logger.info("Experiment dir: %s", root)
    return paths
