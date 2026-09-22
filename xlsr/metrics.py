"""
Section 23 - 32: Research Evaluation Metrics, Reports, Confusion Matrix & Plotting.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless plotting
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

from xlsr.labels import CLASS_NAMES, ID_TO_EMOTION

logger = logging.getLogger(__name__)


def compute_ser_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
) -> Dict[str, float]:
    """
    Compute comprehensive SER metrics:
      - Accuracy (WAR)
      - Macro Precision, Recall, F1
      - Weighted Precision, Recall, F1
      - UAR (Unweighted Average Recall: mean of per-class recalls)
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    acc = float(accuracy_score(y_true, y_pred))
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )

    # Per-class recall to calculate UAR (Unweighted Average Recall)
    _, per_class_recall, _, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(CLASS_NAMES))), average=None, zero_division=0
    )
    uar = float(np.mean(per_class_recall))
    war = acc  # Weighted Average Recall equals accuracy in standard SER definitions

    return {
        "accuracy": acc,
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "weighted_precision": float(weighted_p),
        "weighted_recall": float(weighted_r),
        "weighted_f1": float(weighted_f1),
        "uar": uar,
        "war": war,
    }


def save_confusion_matrix(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    output_dir: Union[Path, str],
) -> Tuple[Path, Path]:
    """
    Generate and save confusion matrix PNG and CSV (Section 26).
    Class order: Neutral, Calm, Happy, Sad, Angry, Fearful, Disgust, Surprised
    """
    out_dir = Path(output_dir) / "predictions"
    out_dir.mkdir(parents=True, exist_ok=True)

    cm = confusion_matrix(
        y_true, y_pred, labels=list(range(len(CLASS_NAMES)))
    )

    # Save CSV
    cm_df = pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES)
    csv_path = out_dir / "confusion_matrix.csv"
    cm_df.to_csv(csv_path, index_label="true_emotion")

    # Plot PNG
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)

    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
        title="Wav2Vec2-XLS-R-300M SER — Confusion Matrix",
        ylabel="True Label",
        xlabel="Predicted Label",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Annotate counts inside matrix cells
    thresh = cm.max() / 2.0 if cm.max() > 0 else 1.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                format(cm[i, j], "d"),
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
            )
    fig.tight_layout()

    png_path = out_dir / "confusion_matrix.png"
    plt.savefig(png_path, dpi=300)
    plt.close(fig)

    logger.info("Confusion matrix saved to %s and %s", csv_path, png_path)
    return png_path, csv_path


def save_classification_report(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    output_dir: Union[Path, str],
) -> Path:
    """Save classification report CSV (Section 27)."""
    out_dir = Path(output_dir) / "predictions"
    out_dir.mkdir(parents=True, exist_ok=True)

    report_dict = classification_report(
        y_true,
        y_pred,
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0,
    )

    rows = []
    for cls_name in CLASS_NAMES:
        if cls_name in report_dict:
            item = report_dict[cls_name]
            rows.append({
                "emotion": cls_name,
                "precision": item["precision"],
                "recall": item["recall"],
                "f1_score": item["f1-score"],
                "support": item["support"],
            })

    report_df = pd.DataFrame(rows)
    csv_path = out_dir / "classification_report.csv"
    report_df.to_csv(csv_path, index=False)
    logger.info("Classification report CSV saved to %s", csv_path)
    return csv_path


def save_test_predictions(
    df: pd.DataFrame,
    y_true: Sequence[int],
    y_pred: Sequence[int],
    probabilities: np.ndarray,
    output_dir: Union[Path, str],
) -> Path:
    """Save detailed test predictions CSV (Section 28)."""
    out_dir = Path(output_dir) / "predictions"
    out_dir.mkdir(parents=True, exist_ok=True)

    confidences = np.max(probabilities, axis=1) if len(probabilities) > 0 else np.ones(len(y_pred))

    pred_df = pd.DataFrame({
        "filepath": df["filepath"] if "filepath" in df else df["abs_filepath"],
        "filename": df["filename"],
        "actor_id": df["actor_id"],
        "true_label": y_true,
        "true_emotion": [ID_TO_EMOTION[int(l)] for l in y_true],
        "predicted_label": y_pred,
        "predicted_emotion": [ID_TO_EMOTION[int(p)] for p in y_pred],
        "confidence": confidences,
    })

    csv_path = out_dir / "test_predictions.csv"
    pred_df.to_csv(csv_path, index=False)
    logger.info("Test predictions CSV saved to %s", csv_path)
    return csv_path


def plot_training_curves(
    history_df: pd.DataFrame,
    output_dir: Union[Path, str],
) -> Dict[str, Path]:
    """
    Generate 3 separate plot figures (Section 29):
      - loss_curve.png
      - macro_f1_curve.png
      - accuracy_curve.png
    """
    out_dir = Path(output_dir) / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)

    epochs = history_df["epoch"]
    paths = {}

    # Plot 1: Loss
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(epochs, history_df["train_loss"], label="Train Loss", marker="o")
    ax.plot(epochs, history_df["val_loss"], label="Validation Loss", marker="s")
    ax.set_title("Training Loss vs Validation Loss")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.tight_layout()
    p1 = out_dir / "loss_curve.png"
    plt.savefig(p1, dpi=300)
    plt.close(fig)
    paths["loss"] = p1

    # Plot 2: Macro-F1
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(epochs, history_df["train_macro_f1"], label="Train Macro-F1", marker="o")
    ax.plot(epochs, history_df["val_macro_f1"], label="Validation Macro-F1", marker="s")
    ax.set_title("Training Macro-F1 vs Validation Macro-F1")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Macro-F1")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.tight_layout()
    p2 = out_dir / "macro_f1_curve.png"
    plt.savefig(p2, dpi=300)
    plt.close(fig)
    paths["macro_f1"] = p2

    # Plot 3: Accuracy
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(epochs, history_df["train_accuracy"], label="Train Accuracy", marker="o")
    ax.plot(epochs, history_df["val_accuracy"], label="Validation Accuracy", marker="s")
    ax.set_title("Training Accuracy vs Validation Accuracy")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Accuracy")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.tight_layout()
    p3 = out_dir / "accuracy_curve.png"
    plt.savefig(p3, dpi=300)
    plt.close(fig)
    paths["accuracy"] = p3

    logger.info("Training curves saved to %s", out_dir)
    return paths
