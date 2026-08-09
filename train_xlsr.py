"""
CLI Training Script for Wav2Vec2-XLS-R-300M SER.

Section 35:
python train_xlsr.py --data_dir ravdess_preprocessed --output_dir outputs/wav2vec2_xlsr_300m
"""

from __future__ import annotations

import argparse
import logging
import os
import random
import sys
from pathlib import Path

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import numpy as np
import torch

from xlsr.config import default_config, save_config
from xlsr.dataset import RAVDESSXLSRDataset
from xlsr.dataset_io import load_ravdess_splits
from xlsr.experiment_dirs import create_experiment_dirs
from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.split_guard import assert_no_actor_leakage
from xlsr.trainer import XLSRTrainer


def set_reproducibility_seed(seed: int = 42) -> None:
    """Set random seeds for Python, NumPy, and PyTorch (Section 33)."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Wav2Vec2-XLS-R-300M SER Model")
    parser.add_argument("--data_dir", type=str, default=str(DEFAULT_DATA_DIR), help="Path to preprocessed RAVDESS dataset")
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory for experiment outputs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size per step")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--encoder_lr", type=float, default=1e-5, help="Learning rate for Wav2Vec2 encoder")
    parser.add_argument("--classifier_lr", type=float, default=1e-4, help="Learning rate for classification head")
    parser.add_argument("--freeze_encoder", action="store_true", help="Freeze Wav2Vec2 encoder (Mode A)")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--mixed_precision", action="store_true", default=True, help="Enable mixed precision training")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--max_train_samples", type=int, default=None, help="Optional sample limit for quick dry-runs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Create output structure and setup logger
    exp_dirs = create_experiment_dirs(args.output_dir)
    log_path = exp_dirs["logs"] / "training.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger("train_xlsr")
    logger.info("Starting Wav2Vec2-XLS-R-300M SER Training")

    # Section 33 — Reproducibility
    set_reproducibility_seed(args.seed)

    # Section 2 & 3 — Load preprocessed splits & verify zero actor leakage
    logger.info("Loading preprocessed dataset from %s", args.data_dir)
    bundle = load_ravdess_splits(args.data_dir)
    assert_no_actor_leakage(bundle)

    # Build configuration dictionary
    config = default_config(freeze_encoder=args.freeze_encoder)
    config.update({
        "data_dir": str(args.data_dir),
        "output_dir": str(args.output_dir),
        "batch_size": args.batch_size,
        "num_epochs": args.epochs,
        "encoder_learning_rate": args.encoder_lr,
        "classifier_learning_rate": args.classifier_lr,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "mixed_precision": args.mixed_precision,
        "seed": args.seed,
    })
    save_config(config, exp_dirs["config"])

    # Prepare PyTorch Datasets
    train_dataset = RAVDESSXLSRDataset(bundle.train, data_dir=bundle.data_dir, max_samples=args.max_train_samples)
    val_dataset = RAVDESSXLSRDataset(bundle.validation, data_dir=bundle.data_dir, max_samples=args.max_train_samples)

    logger.info("Train dataset size: %d | Validation dataset size: %d", len(train_dataset), len(val_dataset))

    # Initialize trainer and launch training
    trainer = XLSRTrainer(config=config, output_dir=args.output_dir)
    result = trainer.run_training(train_dataset, val_dataset)

    logger.info(
        "Training complete! Best Val Macro-F1: %.4f | Total Time: %.1fs | Avg Epoch Time: %.1fs",
        result["best_val_macro_f1"],
        result["total_training_time"],
        result["avg_epoch_time"],
    )
    print("\n" + "=" * 60)
    print("Training Completed Successfully!")
    print(f"Best Validation Macro-F1: {result['best_val_macro_f1']:.4f}")
    print(f"Total Training Time: {result['total_training_time']:.1f} seconds")
    print(f"Experiment Output Directory: {args.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
