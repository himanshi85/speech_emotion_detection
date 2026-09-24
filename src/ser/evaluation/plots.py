"""Training curve plots."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_training_curves(history_path: Path, metrics_dir: Path) -> None:
    df = pd.read_csv(history_path)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.plot(df["epoch"], df["train_loss"], label="train_loss")
    plt.plot(df["epoch"], df["val_loss"], label="val_loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.title("Training vs Validation Loss")
    plt.tight_layout()
    plt.savefig(metrics_dir / "loss_curve.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(df["epoch"], df["train_macro_f1"], label="train_macro_f1")
    plt.plot(df["epoch"], df["val_macro_f1"], label="val_macro_f1")
    plt.xlabel("Epoch")
    plt.ylabel("Macro-F1")
    plt.legend()
    plt.title("Training vs Validation Macro-F1")
    plt.tight_layout()
    plt.savefig(metrics_dir / "macro_f1_curve.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(df["epoch"], df["train_accuracy"], label="train_accuracy")
    plt.plot(df["epoch"], df["val_accuracy"], label="val_accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.title("Training vs Validation Accuracy")
    plt.tight_layout()
    plt.savefig(metrics_dir / "accuracy_curve.png", dpi=150)
    plt.close()
