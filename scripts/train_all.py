#!/usr/bin/env python3
"""Train all 8 SER models sequentially."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ser.core.config import load_model_config
from ser.core.paths import ALL_MODEL_KEYS
from ser.training.trainer import train_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("train_all")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train all SER models")
    parser.add_argument("--skip", nargs="*", default=[], help="Model keys to skip")
    parser.add_argument("--epochs", type=int, default=None)
    args = parser.parse_args()

    failed = []
    for key in ALL_MODEL_KEYS:
        if key in args.skip:
            logger.info("Skipping %s", key)
            continue
        logger.info("========== Training %s ==========", key)
        try:
            overrides = {}
            if args.epochs is not None:
                overrides["num_epochs"] = args.epochs
            cfg = load_model_config(key, overrides=overrides)
            train_model(cfg)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed training %s: %s", key, exc)
            failed.append(key)

    if failed:
        logger.error("Failed models: %s", failed)
        return 1

    logger.info("All models trained. Run: python scripts/compare_results.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
