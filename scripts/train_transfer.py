#!/usr/bin/env python3
"""
Cross-Corpus Transfer Learning Training Script
==============================================
Transfers representations learned from a rich source dataset (e.g., CREMA-D with 64 speakers)
to a smaller target dataset (e.g., SAVEE with 4 speakers) with optional SUPERB-style
Weighted Layer Pooling to overcome small-sample speaker overfitting.
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

from ser.core.config import load_model_config
from ser.training.trainer import train_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("train_transfer")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-corpus transfer learning for Speech Emotion Recognition")
    parser.add_argument("--model_key", type=str, default="hubert", help="Model architecture (e.g. hubert, wavlm, wav2vec2)")
    parser.add_argument("--source_dataset", type=str, default="cremad", help="Source dataset name (e.g. cremad)")
    parser.add_argument("--source_ckpt", type=str, default=None, help="Explicit path to source best_model.pt checkpoint")
    parser.add_argument("--target_dataset", type=str, default="savee", help="Target dataset name (e.g. savee)")
    parser.add_argument("--target_data_dir", type=str, default=None, help="Target preprocessed directory (e.g. savee_preprocessed)")
    parser.add_argument("--output_dir", type=str, default=None, help="Destination directory for enhanced model output")
    parser.add_argument("--layer_pooling", type=str, default="weighted", choices=["weighted", "last"], help="Layer pooling strategy")
    parser.add_argument("--freeze_encoder", action="store_true", help="Freeze encoder weights to prevent overfitting on small target datasets")
    parser.add_argument("--lr", type=float, default=1e-5, help="Fine-tuning learning rate (default: 1e-5)")
    parser.add_argument("--batch_size", type=int, default=None, help="Batch size override")
    parser.add_argument("--epochs", type=int, default=25, help="Number of fine-tuning epochs")
    parser.add_argument("--patience", type=int, default=6, help="Early stopping patience")
    args = parser.parse_args()

    # Resolve source checkpoint
    if args.source_ckpt:
        source_ckpt = Path(args.source_ckpt).resolve()
    else:
        source_ckpt = (
            PROJECT_ROOT
            / "outputs"
            / args.source_dataset
            / args.model_key
            / "checkpoints"
            / "best_model"
            / "model.pt"
        ).resolve()

    if not source_ckpt.exists():
        logger.error("Source checkpoint not found at: %s", source_ckpt)
        return 1

    # Resolve target dataset directory
    if args.target_data_dir:
        target_data_dir = Path(args.target_data_dir).resolve()
    elif (PROJECT_ROOT / "data" / args.target_dataset).exists():
        target_data_dir = (PROJECT_ROOT / "data" / args.target_dataset).resolve()
    else:
        target_data_dir = (PROJECT_ROOT / f"{args.target_dataset}_preprocessed").resolve()
    if not target_data_dir.exists():
        logger.error("Target dataset directory not found at: %s", target_data_dir)
        return 1

    # Resolve output directory
    freeze_tag = "_frozen" if args.freeze_encoder else ""
    tag = f"{args.model_key}_transfer_{args.source_dataset}_{args.layer_pooling}{freeze_tag}"
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else (PROJECT_ROOT / "outputs" / f"{args.target_dataset}_enhanced" / tag).resolve()
    )

    logger.info("==================================================")
    logger.info("Starting Transfer Learning Enhancement")
    logger.info("Model:            %s", args.model_key)
    logger.info("Source Model:     %s (%s)", args.source_dataset, source_ckpt)
    logger.info("Target Dataset:   %s (%s)", args.target_dataset, target_data_dir)
    logger.info("Layer Pooling:    %s", args.layer_pooling)
    logger.info("Freeze Encoder:   %s", args.freeze_encoder)
    logger.info("Learning Rate:    %s", args.lr)
    logger.info("Max Epochs:       %d (patience: %d)", args.epochs, args.patience)
    logger.info("Output Directory: %s", output_dir)
    logger.info("==================================================")

    overrides = {
        "data_dir": str(target_data_dir),
        "output_dir": str(output_dir),
        "pretrained_checkpoint": str(source_ckpt),
        "layer_pooling": args.layer_pooling,
        "freeze_encoder": args.freeze_encoder,
        "learning_rate": args.lr,
        "encoder_learning_rate": 0.0 if args.freeze_encoder else args.lr,
        "classifier_learning_rate": 3e-4 if args.freeze_encoder else (args.lr * 10),
        "num_epochs": args.epochs,
        "early_stopping_patience": args.patience,
    }
    if args.batch_size:
        overrides["batch_size"] = args.batch_size

    cfg = load_model_config(args.model_key, overrides=overrides)
    cfg["display_name"] = f"{cfg.get('display_name', args.model_key)} (Transfer from {args.source_dataset.upper()})"

    try:
        final_results = train_model(cfg)
        logger.info("Transfer learning completed successfully!")
        logger.info("Test Accuracy: %.4f | Macro-F1: %.4f", final_results.get("accuracy", 0.0), final_results.get("macro_f1", 0.0))

        # Update comparison in enhanced output root if applicable
        enhanced_root = output_dir.parent
        try:
            from scripts.compare_results import main as compare_main
            sys_argv_backup = list(sys.argv)
            sys.argv = [
                "compare_results.py",
                "--outputs_root",
                str(enhanced_root),
                "--comparison_dir",
                str(enhanced_root / "comparison"),
            ]
            compare_main()
            sys.argv = sys_argv_backup
        except Exception as cmp_err:
            logger.debug("Comparison update notice: %s", cmp_err)

    except Exception as exc:
        logger.exception("Transfer learning training failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
