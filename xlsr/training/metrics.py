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

from xlsr.data.labels import CLASS_NAMES, ID_TO_EMOTION

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
      - Unweighted Average Recall (UAR / Balanced Accuracy)
      - Per-class F1-scores
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    acc = float(accuracy_score(y_true, y_pred))

    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    p_wt, r_wt, f1_wt, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CLASS_NAMES))))
    with np.errstate(divide="ignore", invalid="ignore"):
        recalls_per_class = np.diag(cm) / cm.sum(axis=1)
        recalls_per_class = np.nan_to_num(recalls_per_class, nan=0.0)
    uar = float(np.mean(recalls_per_class))

    _, _, per_class_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(CLASS_NAMES))), average=None, zero_division=0
    )

    metrics: Dict[str, float] = {
        "accuracy": acc,
        "war": acc,
        "uar": uar,
        "macro_precision": float(p_macro),
        "macro_recall": float(r_macro),
        "macro_f1": float(f1_macro),
        "weighted_precision": float(p_wt),
        "weighted_recall": float(r_wt),
        "weighted_f1": float(f1_wt),
    }

    for idx, name in enumerate(CLASS_NAMES):
        metrics[f"f1_{name}"] = float(per_class_f1[idx])

    return metrics


def save_confusion_matrix(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    output_dir: Union[Path, str],
    class_names: Sequence[str] = CLASS_NAMES,
    normalize: bool = True,
) -> Tuple[Path, Path]:
    """Compute and save both raw/normalized confusion matrix CSV and plot (Section 31)."""
    out_dir = Path(output_dir)
    cm_dir = out_dir / "confusion_matrix"
    cm_dir.mkdir(parents=True, exist_ok=True)

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))
    cm_df = pd.DataFrame(cm, index=class_names, columns=class_names)
    csv_path = cm_dir / "confusion_matrix.csv"
    cm_df.to_csv(csv_path)

    if normalize:
        cm_norm = cm.astype("float") / cm.sum(axis=1, keepdims=True)
        cm_norm = np.nan_to_num(cm_norm, nan=0.0)
        plot_matrix = cm_norm
        fmt = ".2f"
    else:
        plot_matrix = cm
        fmt = "d"

    fig, ax = plt.subplots(figsize=(8, 7))
    cax = ax.matshow(plot_matrix, cmap="Blues", interpolation="nearest")
    fig.colorbar(cax)

    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="left")
    ax.set_yticklabels(class_names)

    ax.set_xlabel("Predicted Emotion", fontweight="bold")
    ax.set_ylabel("True Emotion", fontweight="bold")
    title = "Normalized Confusion Matrix" if normalize else "Raw Confusion Matrix"
    ax.set_title(title, pad=20, fontweight="bold")

    thresh = plot_matrix.max() / 2.0
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            val = plot_matrix[i, j]
            text = f"{val:{fmt}}"
            color = "white" if val > thresh else "black"
            ax.text(j, i, text, ha="center", va="center", color=color, fontsize=10)

    fig.tight_layout()
    plot_path = cm_dir / "confusion_matrix.png"
    fig.savefig(plot_path, dpi=300)
    plt.close(fig)

    logger.info("Saved confusion matrix CSV to %s", csv_path)
    logger.info("Saved confusion matrix plot to %s", plot_path)
    return csv_path, plot_path


def save_classification_report(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    output_dir: Union[Path, str],
    class_names: Sequence[str] = CLASS_NAMES,
) -> Path:
    """Save full classification report text and metrics JSON/CSV (Section 31)."""
    out_dir = Path(output_dir)
    metrics_dir = out_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    report_str = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(class_names))),
        target_names=list(class_names),
        zero_division=0,
    )
    report_path = metrics_dir / "classification_report.txt"
    report_path.write_text(report_str, encoding="utf-8")
    logger.info("Saved classification report to %s", report_path)
    return report_path


def plot_training_curves(
    history: Union[pd.DataFrame, Dict[str, List[float]]],
    output_dir: Union[Path, str],
) -> Path:
    """Generate and save training/validation loss, accuracy, and macro-F1 curves (Section 32)."""
    out_dir = Path(output_dir)
    curves_dir = out_dir / "curves"
    curves_dir.mkdir(parents=True, exist_ok=True)

    if not isinstance(history, pd.DataFrame):
        history = pd.DataFrame(history)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1. Loss curves
    axes[0].plot(history["epoch"], history["train_loss"], label="Train Loss", color="royalblue", lw=2)
    axes[0].plot(history["epoch"], history["val_loss"], label="Val Loss", color="crimson", lw=2)
    axes[0].set_title("Training & Validation Loss", fontweight="bold")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss (Cross-Entropy)")
    axes[0].legend()
    axes[0].grid(True, linestyle="--", alpha=0.5)

    # 2. Accuracy curves
    axes[1].plot(history["epoch"], history["train_accuracy"] * 100, label="Train Acc", color="royalblue", lw=2)
    axes[1].plot(history["epoch"], history["val_accuracy"] * 100, label="Val Acc (WAR)", color="crimson", lw=2)
    if "val_uar" in history.columns:
        axes[1].plot(history["epoch"], history["val_uar"] * 100, label="Val UAR", color="darkorange", linestyle="--", lw=2)
    axes[1].set_title("Training & Validation Accuracy (%)", fontweight="bold")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy (%)")
    axes[1].legend()
    axes[1].grid(True, linestyle="--", alpha=0.5)

    # 3. Macro-F1 curves
    axes[2].plot(history["epoch"], history["train_macro_f1"], label="Train Macro-F1", color="royalblue", lw=2)
    axes[2].plot(history["epoch"], history["val_macro_f1"], label="Val Macro-F1", color="crimson", lw=2)
    axes[2].set_title("Training & Validation Macro-F1", fontweight="bold")
    axes[2].set_xlabel("Epoch")
    axes[2].set_ylabel("Macro-F1 Score")
    axes[2].legend()
    axes[2].grid(True, linestyle="--", alpha=0.5)

    fig.tight_layout()
    plot_path = curves_dir / "training_curves.png"
    fig.savefig(plot_path, dpi=300)
    plt.close(fig)

    logger.info("Saved training curves plot to %s", plot_path)
    return plot_path


def save_test_predictions(
    filenames: Sequence[str],
    y_true: Sequence[int],
    y_pred: Sequence[int],
    y_probs: np.ndarray,
    output_dir: Union[Path, str],
) -> Path:
    """Save test predictions and probabilities CSV (Section 31)."""
    out_dir = Path(output_dir)
    pred_dir = out_dir / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "filename": list(filenames),
        "true_emotion": [ID_TO_EMOTION[int(y)] for y in y_true],
        "predicted_emotion": [ID_TO_EMOTION[int(y)] for y in y_pred],
        "true_id": list(y_true),
        "predicted_id": list(y_pred),
    }

    for idx, emotion in enumerate(CLASS_NAMES):
        data[f"prob_{emotion}"] = y_probs[:, idx]

    df = pd.DataFrame(data)
    pred_path = pred_dir / "test_predictions.csv"
    df.to_csv(pred_path, index=False)
    logger.info("Saved test predictions to %s", pred_path)
    return pred_path
