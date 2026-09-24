#!/usr/bin/env python3
"""Evaluate a trained checkpoint on train/val/test splits.

Usage:
    python scripts/evaluate.py --model hubert --checkpoint best
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import torch
from torch.utils.data import DataLoader

from ser.core.config import load_model_config
from ser.core.paths import ALL_MODEL_KEYS
from ser.core.registry import build_collator, build_model
from ser.data.class_weights import compute_class_weights
from ser.data.torch_dataset import RAVDESSSERDataset
from ser.evaluation.runner import evaluate_split, save_split_results
from ser.training.experiment import create_experiment_dirs
from ser.training.trainer import load_checkpoint_model
from ser.data.dataset import load_ravdess_splits

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("evaluate")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate SER checkpoint")
    parser.add_argument("--model", required=True, choices=ALL_MODEL_KEYS)
    parser.add_argument("--checkpoint", choices=["best", "final"], default="best")
    parser.add_argument("--splits", nargs="+", default=["train", "validation", "test"])
    parser.add_argument("--data_dir", type=str, default=None, help="Dataset directory")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
    parser.add_argument("--dataset", type=str, default=None, help="Dataset name shortcut")
    args = parser.parse_args()

    overrides = {}
    if args.data_dir:
        overrides["data_dir"] = args.data_dir
    if args.output_dir:
        overrides["output_dir"] = args.output_dir

    cfg = load_model_config(args.model, overrides=overrides, dataset=args.dataset)
    paths = create_experiment_dirs(cfg["output_dir"])
    ckpt_dir = paths["best_model"] if args.checkpoint == "best" else paths["final_model"]

    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        else "cpu"
    )
    model = build_model(cfg).to(device)
    load_checkpoint_model(ckpt_dir, model)

    bundle = load_ravdess_splits(cfg.get("data_dir"))
    collator = build_collator(cfg)
    batch_size = int(cfg.get("batch_size", 4))
    class_weights = compute_class_weights(bundle.train) if cfg.get("class_weights", True) else None
    display_name = cfg.get("display_name", args.model)

    split_map = {
        "train": bundle.train,
        "validation": bundle.validation,
        "test": bundle.test,
    }

    for split_name in args.splits:
        if split_name not in split_map:
            continue
        loader = DataLoader(
            RAVDESSSERDataset(split_map[split_name], split_name),
            batch_size=batch_size,
            collate_fn=collator,
        )
        m, report, yt, yp, conf, meta = evaluate_split(model, loader, device, class_weights)
        save_split_results(paths["root"], split_name, m, report, yt, yp, conf, meta, display_name)
        logger.info("%s: macro_f1=%.4f", split_name, m["macro_f1"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
