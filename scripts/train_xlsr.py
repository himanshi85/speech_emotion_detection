"""
CLI Training Script for Wav2Vec2-XLS-R-300M SER.

Usage:
    python scripts/train_xlsr.py --data_dir ravdess_preprocessed --output_dir outputs/wav2vec2_xlsr_300m
"""

from __future__ import annotations

import argparse
import logging
import os
import random
import sys
from pathlib import Path

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import numpy as np
import torch

from xlsr.core.config import default_config, save_config
from xlsr.core.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.data.dataset import RAVDESSXLSRDataset, load_ravdess_splits
from xlsr.data.split import assert_no_actor_leakage
from xlsr.training.experiment import create_experiment_dirs
from xlsr.training.trainer import XLSRTrainer


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
    parser = argparse.ArgumentParser(
        description="Train Wav2Vec2-XLS-R-300M for Speech Emotion Recognition on RAVDESS",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--data_dir", type=str, default=str(DEFAULT_DATA_DIR), help="Path to preprocessed dataset")
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Path to save experiment outputs")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size per training step")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--encoder_lr", type=float, default=1e-5, help="Learning rate for XLS-R encoder")
    parser.add_argument("--classifier_lr", type=float, default=1e-4, help="Learning rate for classification head")
    parser.add_argument("--weight_decay", type=float, default=0.01, help="Weight decay for AdamW")
    parser.add_argument("--dropout", type=float, default=0.3, help="Dropout probability for classification head")
    parser.add_argument("--freeze_encoder", action="store_true", default=False, help="Freeze XLS-R encoder parameters")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience (epochs)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Create experiment folder structure
    output_path = Path(args.output_dir).resolve()
    dirs = create_experiment_dirs(output_path)

    # Configure logging
    log_file = dirs["logs"] / "training.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger("train_xlsr")
    logger.info("Starting Wav2Vec2-XLS-R-300M SER Training")
    logger.info("Output directory: %s", output_path)

    # Set seed
    set_reproducibility_seed(args.seed)
    logger.info("Set random seed: %d", args.seed)

    # Load dataset splits and verify zero actor leakage
    data_path = Path(args.data_dir).resolve()
    logger.info("Loading dataset splits from %s", data_path)
    bundle = load_ravdess_splits(data_path)

    logger.info("Verifying actor-independent split (Section 3 Guard)...")
    assert_no_actor_leakage(bundle)
    logger.info("Zero actor leakage verified: Train (16 actors), Val (4 actors), Test (4 actors)")

    # Build config dictionary
    config = default_config()
    config.update({
        "num_epochs": args.epochs,
        "batch_size": args.batch_size,
        "gradient_accumulation_steps": args.grad_accum,
        "encoder_learning_rate": args.encoder_lr,
        "classifier_learning_rate": args.classifier_lr,
        "weight_decay": args.weight_decay,
        "dropout": args.dropout,
        "freeze_encoder": args.freeze_encoder,
        "seed": args.seed,
        "early_stopping_patience": args.patience,
    })

    # Save experiment config
    save_config(config, dirs["config"] / "experiment_config.yaml")

    # Instantiate datasets
    train_dataset = RAVDESSXLSRDataset(bundle.train_df)
    val_dataset = RAVDESSXLSRDataset(bundle.val_df)

    logger.info("Train samples: %d | Validation samples: %d", len(train_dataset), len(val_dataset))

    # Initialize trainer and train
    trainer = XLSRTrainer(config=config, output_dir=output_path)
    results = trainer.run_training(train_dataset=train_dataset, val_dataset=val_dataset)

    logger.info("Training complete!")
    logger.info("Best Validation Macro-F1: %.4f", results["best_val_macro_f1"])
    logger.info("Total Training Time: %.1f seconds", results["total_training_time"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
