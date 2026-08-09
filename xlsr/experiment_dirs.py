"""
Create and manage the experiment output directory for training results.

All XLS-R runs store artifacts under:
    outputs/wav2vec2_xlsr_300m/
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

from xlsr.paths import DEFAULT_OUTPUT_DIR, OUTPUT_SUBDIRS

logger = logging.getLogger(__name__)


def create_experiment_dirs(output_dir: Path | str | None = None) -> Dict[str, Path]:
    """
    Ensure the experiment folder tree exists and return key paths.

    Structure:
        outputs/wav2vec2_xlsr_300m/
        ├── config.yaml          (written later)
        ├── checkpoints/
        │   ├── best_model/
        │   └── final_model/
        ├── metrics/
        ├── predictions/
        └── logs/
    """
    root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    paths: Dict[str, Path] = {"root": root}
    for rel in OUTPUT_SUBDIRS:
        path = root / rel
        path.mkdir(parents=True, exist_ok=True)
        key = rel.replace("/", "_")
        paths[key] = path

    paths["checkpoints"] = root / "checkpoints"
    paths["best_model"] = root / "checkpoints" / "best_model"
    paths["final_model"] = root / "checkpoints" / "final_model"
    paths["metrics"] = root / "metrics"
    paths["predictions"] = root / "predictions"
    paths["logs"] = root / "logs"
    paths["config"] = root / "config.yaml"
    paths["training_log"] = root / "logs" / "training.log"

    logger.info("Experiment output directory ready: %s", root)
    return paths
