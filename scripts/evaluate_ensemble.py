#!/usr/bin/env python3
"""Evaluate an ensemble of SER models via Soft Voting.

Usage:
    python scripts/evaluate_ensemble.py --models wavlm wav2vec2 mfcc_cnn_bilstm --split test
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ser.core.config import load_model_config
from ser.core.registry import build_collator, build_model
from ser.data.torch_dataset import RAVDESSSERDataset
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
from ser.evaluation.runner import _forward_batch
from ser.training.trainer import load_checkpoint_model
from xlsr.data.dataset import load_ravdess_splits
from xlsr.data.labels import CLASS_NAMES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ensemble")


def get_model_probabilities(
    model_key: str,
    ckpt_dir: Path,
    bundle_split_df: pd.DataFrame,
    data_dir: str | None,
    device: torch.device,
) -> tuple[np.ndarray, list[int], dict]:
    overrides = {}
    if data_dir:
        overrides["data_dir"] = data_dir

    label_map_file = ckpt_dir / "label_mapping.json"
    if label_map_file.exists():
        mapping = json.loads(label_map_file.read_text(encoding="utf-8"))
        overrides["num_classes"] = len(mapping)
    elif data_dir:
        lbl_file = Path(data_dir) / "metadata" / "labels.json"
        if lbl_file.exists():
            mapping = json.loads(lbl_file.read_text(encoding="utf-8"))
            overrides["num_classes"] = len(mapping)

    cfg = load_model_config(model_key, overrides=overrides)

    model = build_model(cfg).to(device)
    load_checkpoint_model(ckpt_dir, model)
    model.eval()

    collator = build_collator(cfg)
    loader = DataLoader(
        RAVDESSSERDataset(bundle_split_df, "test"),
        batch_size=int(cfg.get("batch_size", 4)),
        shuffle=False,
        collate_fn=collator,
        num_workers=0,
    )

    all_probs = []
    y_true = []
    meta_all = {"filepath": [], "filename": [], "actor_id": [], "emotion": [], "split": ""}

    with torch.no_grad():
        for batch in tqdm(loader, desc=f"evaluating {model_key}", leave=False):
            out, labels = _forward_batch(model, batch, device, None)
            probs = F.softmax(out["logits"], dim=-1)
            all_probs.append(probs.cpu().numpy())
            y_true.extend(labels.cpu().tolist())
            for k in ("filepath", "filename", "actor_id", "emotion"):
                meta_all[k].extend(batch["meta"][k])
            meta_all["split"] = batch["meta"]["split"]

    return np.concatenate(all_probs, axis=0), y_true, meta_all


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensemble evaluation of SER models")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["wavlm", "wav2vec2", "mfcc_cnn_bilstm"],
        help="List of model keys to ensemble",
    )
    parser.add_argument("--weights", nargs="+", type=float, default=None)
    parser.add_argument("--split", choices=["test", "validation"], default="test")
    parser.add_argument("--data_dir", type=str, default=None)
    parser.add_argument("--outputs_root", type=str, default=None, help="Root folder for model checkpoints")
    parser.add_argument("--output_dir", type=str, default=None, help="Directory to save ensemble outputs")
    args = parser.parse_args()

    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        else "cpu"
    )
    logger.info("Using device: %s", device)

    bundle = load_ravdess_splits(args.data_dir)
    split_df = bundle.test if args.split == "test" else bundle.validation

    labels_file = bundle.data_dir / "metadata" / "labels.json"
    if labels_file.exists():
        label_mapping = json.loads(labels_file.read_text(encoding="utf-8"))
        id_to_emotion = {int(v): k for k, v in label_mapping.items()}
        class_names = [id_to_emotion[i] for i in range(len(label_mapping))]
    else:
        class_names = list(CLASS_NAMES)

    weights = args.weights
    if weights is None:
        weights = [1.0 / len(args.models)] * len(args.models)
    else:
        norm = sum(weights)
        weights = [w / norm for w in weights]

    model_probs_list = []
    individual_metrics = {}
    y_true_ref = None
    meta_ref = None

    for idx, model_key in enumerate(args.models):
        overrides = {}
        if args.data_dir:
            overrides["data_dir"] = str(Path(args.data_dir).resolve())
        if args.outputs_root:
            overrides["output_dir"] = str(Path(args.outputs_root).resolve() / model_key)
        cfg = load_model_config(model_key, overrides=overrides)
        ckpt_dir = Path(cfg["output_dir"]) / "checkpoints" / "best_model"
        if not ckpt_dir.exists() and args.outputs_root:
            ckpt_dir = Path(args.outputs_root).resolve() / model_key / "checkpoints" / "best_model"
        if not ckpt_dir.exists():
            ckpt_dir = PROJECT_ROOT / "outputs" / "ravdess" / model_key / "checkpoints" / "best_model"
        if not ckpt_dir.exists():
            raise FileNotFoundError(f"Checkpoint not found for {model_key} at {ckpt_dir}")

        probs, y_true, meta = get_model_probabilities(
            model_key, ckpt_dir, split_df, args.data_dir, device
        )
        model_probs_list.append(probs)
        if y_true_ref is None:
            y_true_ref = y_true
            meta_ref = meta

        preds = np.argmax(probs, axis=1).tolist()
        m = compute_metrics(y_true, preds)
        individual_metrics[model_key] = {
            "accuracy": m["accuracy"],
            "macro_f1": m["macro_f1"],
            "uar": m["uar"],
            "weight": weights[idx],
        }
        logger.info(
            "Individual [%s]: Acc=%.4f, Macro-F1=%.4f (weight=%.2f)",
            model_key,
            m["accuracy"],
            m["macro_f1"],
            weights[idx],
        )

    # Soft Voting
    ensemble_probs = np.zeros_like(model_probs_list[0])
    for w, p in zip(weights, model_probs_list):
        ensemble_probs += w * p

    ensemble_preds = np.argmax(ensemble_probs, axis=1).tolist()
    confidences = np.max(ensemble_probs, axis=1).tolist()

    metrics = compute_metrics(y_true_ref, ensemble_preds)
    report = sklearn_classification_report_dict(y_true_ref, ensemble_preds, class_names)
    cm = sklearn_confusion_matrix(y_true_ref, ensemble_preds)

    if args.output_dir:
        out_dir = Path(args.output_dir)
    elif args.outputs_root:
        out_dir = Path(args.outputs_root) / "ensemble"
    else:
        out_dir = Path("outputs/ravdess/ensemble")
    out_dir.mkdir(parents=True, exist_ok=True)

    save_predictions_csv(out_dir / "predictions.csv", meta_ref, y_true_ref, ensemble_preds, confidences, id_to_emotion=id_to_emotion)
    save_classification_report_csv(out_dir / "classification_report.csv", report, class_names=class_names)
    save_confusion_matrix_csv(out_dir / "confusion_matrix.csv", cm, class_names=class_names)
    save_confusion_matrix_png(
        out_dir / "confusion_matrix.png",
        cm,
        title=f"Ensemble ({'+'.join(args.models)}) — {args.split}",
        class_names=class_names,
    )

    summary = {
        "ensemble_models": args.models,
        "weights": weights,
        "split": args.split,
        "ensemble_metrics": metrics,
        "individual_metrics": individual_metrics,
    }
    (out_dir / "ensemble_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    logger.info("==========================================")
    logger.info("🎉 ENSEMBLE TEST ACCURACY: %.4f (%.2f%%)", metrics["accuracy"], metrics["accuracy"] * 100)
    logger.info("🎉 ENSEMBLE MACRO-F1:      %.4f", metrics["macro_f1"])
    logger.info("🎉 ENSEMBLE UAR:           %.4f", metrics["uar"])
    logger.info("==========================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
