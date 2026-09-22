"""SER evaluation metrics."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def compute_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_precision": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "weighted_recall": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "uar": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "war": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def sklearn_classification_report_dict(
    y_true: List[int], y_pred: List[int], class_names: List[str]
) -> Dict:
    return classification_report(
        y_true, y_pred, target_names=class_names, output_dict=True, zero_division=0
    )


def sklearn_confusion_matrix(
    y_true: List[int], y_pred: List[int], labels: List[int] | None = None
) -> np.ndarray:
    return confusion_matrix(y_true, y_pred, labels=labels)
