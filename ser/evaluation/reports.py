"""Save classification reports, confusion matrices, predictions."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from xlsr.data.labels import CLASS_NAMES, ID_TO_EMOTION


def save_predictions_csv(
    path: Path,
    meta: Dict,
    y_true: List[int],
    y_pred: List[int],
    confidences: List[float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(len(y_true)):
        rows.append(
            {
                "filepath": meta["filepath"][i],
                "filename": meta["filename"][i],
                "actor_id": meta["actor_id"][i],
                "split": meta.get("split", ""),
                "true_label": y_true[i],
                "true_emotion": ID_TO_EMOTION[y_true[i]],
                "predicted_label": y_pred[i],
                "predicted_emotion": ID_TO_EMOTION[y_pred[i]],
                "confidence": confidences[i],
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def save_classification_report_csv(path: Path, report_dict: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in CLASS_NAMES:
        if name in report_dict:
            r = report_dict[name]
            rows.append(
                {
                    "emotion": name,
                    "precision": r["precision"],
                    "recall": r["recall"],
                    "f1_score": r["f1-score"],
                    "support": int(r["support"]),
                }
            )
    for avg in ("macro avg", "weighted avg"):
        if avg in report_dict:
            r = report_dict[avg]
            rows.append(
                {
                    "emotion": avg,
                    "precision": r["precision"],
                    "recall": r["recall"],
                    "f1_score": r["f1-score"],
                    "support": int(r["support"]),
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)


def save_confusion_matrix_csv(path: Path, cm: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [n.capitalize() for n in CLASS_NAMES]
    df = pd.DataFrame(cm, index=labels, columns=labels)
    df.to_csv(path)


def save_confusion_matrix_png(path: Path, cm: np.ndarray, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [n.capitalize() for n in CLASS_NAMES]
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(len(labels)),
        yticks=np.arange(len(labels)),
        xticklabels=labels,
        yticklabels=labels,
        title=title,
        ylabel="True",
        xlabel="Predicted",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    thresh = cm.max() / 2.0 if cm.max() > 0 else 0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black",
            )
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
