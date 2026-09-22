#!/usr/bin/env python3
"""Train a single SER model.

Usage:
    python scripts/train.py --model hubert
    python scripts/train.py --model mfcc_lstm --epochs 50
"""

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
logger = logging.getLogger("train")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train SER model on RAVDESS")
    parser.add_argument("--model", required=True, choices=ALL_MODEL_KEYS, help="Model key")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--freeze_encoder", action="store_true")
    parser.add_argument("--data_dir", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--num_classes", type=int, default=None)
    parser.add_argument("--learning_rate", type=float, default=None)
    args = parser.parse_args()

    overrides = {}
    if args.epochs is not None:
        overrides["num_epochs"] = args.epochs
    if args.batch_size is not None:
        overrides["batch_size"] = args.batch_size
    if args.freeze_encoder:
        overrides["freeze_encoder"] = True
    if args.data_dir:
        overrides["data_dir"] = args.data_dir
    if args.output_dir:
        overrides["output_dir"] = args.output_dir
    if args.num_classes is not None:
        overrides["num_classes"] = args.num_classes
    if args.learning_rate is not None:
        overrides["learning_rate"] = args.learning_rate
        overrides["classifier_learning_rate"] = args.learning_rate

    cfg = load_model_config(args.model, overrides=overrides)
    logger.info("Training model: %s", cfg.get("display_name", args.model))
    train_model(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
