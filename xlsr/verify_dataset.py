#!/usr/bin/env python3
"""
Verify Section 2: load existing ravdess_preprocessed splits and prepare output dirs.

Usage (from project root):
    python -m xlsr.verify_dataset
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.dataset_io import (
    load_ravdess_splits,
    verify_actor_independent_split,
    write_dataset_summary,
)
from xlsr.experiment_dirs import create_experiment_dirs
from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify existing RAVDESS dataset load")
    parser.add_argument(
        "--data_dir",
        type=str,
        default=str(DEFAULT_DATA_DIR),
        help="Path to ravdess_preprocessed",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="Path for training results (outputs/wav2vec2_xlsr_300m)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("verify_dataset")

    # Training results folder (created now so all later stages write here)
    exp_paths = create_experiment_dirs(args.output_dir)
    logger.info("Training results will be stored under: %s", exp_paths["root"])

    bundle = load_ravdess_splits(args.data_dir)
    ok, issues = verify_actor_independent_split(bundle, strict=True)
    logger.info("Actor-independent split OK: %s", ok)

    summary_path = write_dataset_summary(
        bundle,
        exp_paths["metrics"] / "dataset_summary.txt",
    )

    logger.info("Sizes: %s", bundle.sizes)
    logger.info("Summary: %s", summary_path)
    logger.info("Section 2 verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
