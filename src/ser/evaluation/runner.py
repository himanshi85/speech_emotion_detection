"""Run evaluation on a split and save all artifacts."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

from ser.evaluation.metrics import (
    compute_metrics,
    sklearn_classification_report_dict,
    sklearn_confusion_matrix,
)
from ser.evaluation.reports import (
    save_classification_report_csv,
    save_confusion_matrix_csv,
    save_confusion_matrix_png,
    save_predictions_csv,
)
from ser.models.base import BaseSERModel
from xlsr.data.labels import CLASS_NAMES

logger = logging.getLogger(__name__)


def _forward_batch(model: BaseSERModel, batch: Dict, device: torch.device, class_weights):
    labels = batch["labels"].to(device)
    kw = {"labels": labels, "class_weights": class_weights}
    mask = batch.get("attention_mask")
    if mask is not None:
        mask = mask.to(device)
    if "input_values" in batch:
        out = model(
            input_values=batch["input_values"].to(device),
            attention_mask=mask,
            **kw,
        )
    else:
        out = model(
            mfcc=batch["mfcc"].to(device),
            attention_mask=mask,
            **kw,
        )
    return out, labels


@torch.no_grad()
def evaluate_split(
    model: BaseSERModel,
    loader: DataLoader,
    device: torch.device,
    class_weights: Optional[torch.Tensor] = None,
    class_names: Optional[List[str]] = None,
) -> Tuple[Dict[str, float], Dict, List[int], List[int], List[float], Dict]:
    model.eval()
    cw = class_weights.to(device) if class_weights is not None else None
    y_true, y_pred, confidences = [], [], []
    meta_all = {"filepath": [], "filename": [], "actor_id": [], "emotion": [], "split": ""}
    total_loss = 0.0
    n_batches = 0

    for batch in tqdm(loader, desc="eval", leave=False):
        out, labels = _forward_batch(model, batch, device, cw)
        logits = out["logits"]
        probs = F.softmax(logits, dim=-1)
        preds = logits.argmax(dim=-1)
        if out["loss"] is not None:
            total_loss += float(out["loss"].item())
            n_batches += 1

        y_true.extend(labels.cpu().tolist())
        y_pred.extend(preds.cpu().tolist())
        confidences.extend(probs.max(dim=-1).values.cpu().tolist())
        for k in ("filepath", "filename", "actor_id", "emotion"):
            meta_all[k].extend(batch["meta"][k])
        meta_all["split"] = batch["meta"]["split"]

    names = class_names if class_names is not None else CLASS_NAMES
    metrics = compute_metrics(y_true, y_pred)
    if n_batches:
        metrics["loss"] = total_loss / n_batches
    report = sklearn_classification_report_dict(y_true, y_pred, names)
    return metrics, report, y_true, y_pred, confidences, meta_all


def save_split_results(
    output_dir: Path,
    split_name: str,
    metrics: Dict[str, float],
    report: Dict,
    y_true: List[int],
    y_pred: List[int],
    confidences: List[float],
    meta: Dict,
    display_name: str,
    class_names: Optional[List[str]] = None,
    id_to_emotion: Optional[Dict[int, str]] = None,
) -> None:
    split_dir = output_dir / "predictions" / split_name
    names = class_names if class_names is not None else CLASS_NAMES
    label_indices = list(range(len(names)))
    cm = sklearn_confusion_matrix(y_true, y_pred, labels=label_indices)
    save_predictions_csv(split_dir / "predictions.csv", meta, y_true, y_pred, confidences, id_to_emotion=id_to_emotion)
    save_classification_report_csv(split_dir / "classification_report.csv", report, class_names=names)
    save_confusion_matrix_csv(split_dir / "confusion_matrix.csv", cm, class_names=names)
    save_confusion_matrix_png(
        split_dir / "confusion_matrix.png",
        cm,
        title=f"{display_name} — {split_name}",
        class_names=names,
    )
    logger.info("%s %s macro_f1=%.4f acc=%.4f", split_name, display_name, metrics["macro_f1"], metrics["accuracy"])
