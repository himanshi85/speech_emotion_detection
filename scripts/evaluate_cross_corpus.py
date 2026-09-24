#!/usr/bin/env python3
"""
Cross-Corpus SER Evaluation Benchmark Suite
============================================
Evaluates a Speech Emotion Recognition model trained on one corpus (e.g. CREMA-D)
directly on unseen target corpora (e.g. RAVDESS, SAVEE, TESS) zero-shot (without
any target-corpus fine-tuning).

This is the definitive gold standard academic test for:
1. Domain Generalization & Acoustic Invariance
2. Cross-Corpus Emotion Recognition Accuracy & UAR
3. Vocal Timbre / Speaker Independence
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ser.core.config import load_model_config
from ser.core.registry import build_collator, build_model
from ser.data.torch_dataset import RAVDESSSERDataset
from ser.evaluation.metrics import compute_metrics
from ser.evaluation.runner import _forward_batch
from ser.training.trainer import load_checkpoint_model
from xlsr.data.dataset import load_ravdess_splits

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("cross_corpus")

# Canonical Emotion Ontology
CANONICAL_MAP = {
    # Anger
    "angry": "angry",
    "anger": "angry",
    # Disgust
    "disgust": "disgust",
    # Fear
    "fear": "fear",
    "fearful": "fear",
    # Happiness
    "happy": "happy",
    "happiness": "happy",
    # Neutral
    "neutral": "neutral",
    # Sadness
    "sad": "sad",
    "sadness": "sad",
    # Surprise
    "surprise": "surprise",
    "surprised": "surprise",
    "pleasant_surprise": "surprise",
    # Calm (RAVDESS-specific)
    "calm": "calm",
}

DATASET_LABEL_MAPPINGS = {
    "cremad": {
        "neutral": 0,
        "happy": 1,
        "sad": 2,
        "angry": 3,
        "fearful": 4,
        "disgust": 5,
    },
    "ravdess": {
        "neutral": 0,
        "calm": 1,
        "happy": 2,
        "sad": 3,
        "angry": 4,
        "fearful": 5,
        "disgust": 6,
        "surprised": 7,
    },
    "savee": {
        "anger": 0,
        "disgust": 1,
        "fear": 2,
        "happiness": 3,
        "neutral": 4,
        "sadness": 5,
        "surprise": 6,
    },
    "tess": {
        "angry": 0,
        "disgust": 1,
        "fear": 2,
        "happy": 3,
        "neutral": 4,
        "pleasant_surprise": 5,
        "sad": 6,
    },
}


def canonicalize(emotion_str: str) -> str:
    return CANONICAL_MAP.get(str(emotion_str).strip().lower(), str(emotion_str).strip().lower())


def resolve_model_and_config(ckpt_path: Path) -> Tuple[torch.nn.Module, Dict[str, Any], Dict[str, int]]:
    """Loads model, config, and source label mapping from checkpoint path."""
    ckpt_path = ckpt_path.resolve()
    if ckpt_path.is_dir():
        model_file = ckpt_path / "checkpoints" / "best_model" / "model.pt"
        if not model_file.exists():
            model_file = ckpt_path / "model.pt"
    else:
        model_file = ckpt_path

    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found at: {model_file}")

    ckpt_dir = model_file.parent

    # Check for explicit label_mapping.json
    source_label_mapping = None
    for search_dir in [ckpt_dir, ckpt_dir.parent, ckpt_dir.parent.parent]:
        lm_file = search_dir / "label_mapping.json"
        if lm_file.exists():
            source_label_mapping = json.loads(lm_file.read_text(encoding="utf-8"))
            break

    ckpt_dict = torch.load(model_file, map_location="cpu", weights_only=False)
    cfg = None
    if isinstance(ckpt_dict, dict) and "config" in ckpt_dict:
        cfg = dict(ckpt_dict["config"])

    if cfg is None:
        # Fallback config inference
        cfg = load_model_config("hubert")

    if source_label_mapping is None:
        # Try inferring from dataset name in cfg
        data_dir = cfg.get("data_dir", "")
        for dname, dmap in DATASET_LABEL_MAPPINGS.items():
            if dname in str(data_dir).lower() or dname in str(ckpt_path).lower():
                source_label_mapping = dmap
                break
        if source_label_mapping is None:
            source_label_mapping = DATASET_LABEL_MAPPINGS["cremad"]

    cfg["num_classes"] = len(source_label_mapping)
    device = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))
    model = build_model(cfg).to(device)

    if isinstance(ckpt_dict, dict) and "model_state_dict" in ckpt_dict:
        model.load_state_dict(ckpt_dict["model_state_dict"])
    elif isinstance(ckpt_dict, dict) and "state_dict" in ckpt_dict:
        model.load_state_dict(ckpt_dict["state_dict"])
    else:
        model.load_state_dict(ckpt_dict)

    model.eval()
    return model, cfg, source_label_mapping


def evaluate_single_corpus(
    model: torch.nn.Module,
    cfg: Dict[str, Any],
    source_label_mapping: Dict[str, int],
    source_name: str,
    target_name: str,
    target_split: str = "test",
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Evaluates the source model zero-shot on target dataset."""
    target_data_dir = PROJECT_ROOT / "data" / target_name
    if not target_data_dir.exists():
        target_data_dir = PROJECT_ROOT / f"{target_name}_preprocessed"
    if not target_data_dir.exists():
        raise FileNotFoundError(f"Target data directory not found: {target_data_dir}")

    bundle = load_ravdess_splits(target_data_dir)
    if target_split == "test":
        target_df = bundle.test.copy()
    elif target_split == "validation":
        target_df = bundle.validation.copy()
    elif target_split == "train":
        target_df = bundle.train.copy()
    elif target_split == "full":
        target_df = pd.concat([bundle.train, bundle.validation, bundle.test], ignore_index=True)
    else:
        raise ValueError(f"Unknown split: {target_split}")

    # Build canonical source mapping: canonical_emotion -> source_class_idx
    canonical_to_source_idx = {}
    for raw_label, idx in source_label_mapping.items():
        canonical_to_source_idx[canonicalize(raw_label)] = idx

    # Target label mapping
    target_label_mapping = DATASET_LABEL_MAPPINGS.get(target_name, {})
    canonical_to_target_raw = {}
    for raw_label in target_label_mapping.keys():
        canonical_to_target_raw[canonicalize(raw_label)] = raw_label

    # Identify shared canonical emotions
    shared_canonical = sorted(list(set(canonical_to_source_idx.keys()) & set(canonical_to_target_raw.keys())))
    logger.info("Shared canonical emotions between %s and %s: %s", source_name, target_name, shared_canonical)

    # Filter target dataframe to shared emotions
    target_df["canonical_emotion"] = target_df["emotion"].apply(canonicalize)
    filtered_df = target_df[target_df["canonical_emotion"].isin(shared_canonical)].copy()
    logger.info("Evaluating on %d clips (filtered from %d clips in %s '%s')", len(filtered_df), len(target_df), target_name, target_split)

    # Map each target row's canonical emotion to the source model's class index
    filtered_df["eval_label"] = filtered_df["canonical_emotion"].apply(lambda e: canonical_to_source_idx[e])
    filtered_df["label"] = filtered_df["eval_label"]

    device = next(model.parameters()).device
    collator = build_collator(cfg)
    loader = DataLoader(
        RAVDESSSERDataset(filtered_df, target_split),
        batch_size=cfg.get("batch_size", 16),
        shuffle=False,
        collate_fn=collator,
        num_workers=0,
    )

    all_preds = []
    all_targets = []
    all_logits = []

    # Identify source class indices corresponding to the shared set
    shared_source_indices = [canonical_to_source_idx[c] for c in shared_canonical]
    source_idx_to_eval_idx = {src_idx: i for i, src_idx in enumerate(shared_source_indices)}

    with torch.no_grad():
        for batch in tqdm(loader, desc=f"Evaluating {source_name} -> {target_name}"):
            outputs, _ = _forward_batch(model, batch, device, class_weights=None)
            logits = outputs["logits"] if isinstance(outputs, dict) else (outputs.logits if hasattr(outputs, "logits") else outputs)
            all_logits.append(logits.cpu())

            # Closed-set evaluation: restrict logits to shared classes
            sub_logits = logits[:, shared_source_indices]
            sub_preds = torch.argmax(sub_logits, dim=-1).cpu().numpy()
            # Map sub_pred back to the shared canonical index
            pred_source_indices = [shared_source_indices[p] for p in sub_preds]
            eval_preds = [source_idx_to_eval_idx[p] for p in pred_source_indices]

            targets = batch["labels"].numpy()
            eval_targets = [source_idx_to_eval_idx[t] for t in targets]

            all_preds.extend(eval_preds)
            all_targets.extend(eval_targets)

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    # Compute metrics over shared canonical classes
    metrics = compute_metrics(all_targets, all_preds)
    report_dict = classification_report(all_targets, all_preds, target_names=shared_canonical, output_dict=True, zero_division=0)
    cm = confusion_matrix(all_targets, all_preds, labels=list(range(len(shared_canonical))))

    # Compute UAR
    per_class_recalls = []
    for i in range(len(shared_canonical)):
        class_total = cm[i].sum()
        if class_total > 0:
            per_class_recalls.append(cm[i, i] / class_total)
    uar = float(np.mean(per_class_recalls)) if per_class_recalls else 0.0

    result = {
        "source_dataset": source_name,
        "target_dataset": target_name,
        "target_split": target_split,
        "total_clips": len(filtered_df),
        "num_shared_classes": len(shared_canonical),
        "shared_classes": shared_canonical,
        "accuracy": float(metrics["accuracy"]),
        "macro_f1": float(metrics["macro_f1"]),
        "macro_precision": float(metrics["macro_precision"]),
        "macro_recall": float(metrics["macro_recall"]),
        "uar": uar,
        "war": float(metrics["accuracy"]),
    }

    if output_dir:
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save metrics JSON
        (output_dir / "zero_shot_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

        # Save Classification Report CSV
        report_df = pd.DataFrame(report_dict).transpose()
        report_df.to_csv(output_dir / "classification_report.csv")

        # Save Confusion Matrix CSV
        cm_df = pd.DataFrame(cm, index=shared_canonical, columns=shared_canonical)
        cm_df.to_csv(output_dir / "confusion_matrix.csv")

        # Save Confusion Matrix PNG
        fig, ax = plt.subplots(figsize=(7, 6))
        cax = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        fig.colorbar(cax)
        tick_marks = np.arange(len(shared_canonical))
        ax.set_xticks(tick_marks)
        ax.set_xticklabels(shared_canonical, rotation=45, ha="right")
        ax.set_yticks(tick_marks)
        ax.set_yticklabels(shared_canonical)
        thresh = cm.max() / 2.0 if cm.max() > 0 else 1.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, format(cm[i, j], "d"),
                        ha="center", va="center",
                        color="white" if cm[i, j] > thresh else "black")
        ax.set_title(f"Zero-Shot: {source_name.upper()} -> {target_name.upper()} ({result['accuracy']*100:.1f}%)")
        ax.set_ylabel("Ground Truth")
        ax.set_xlabel("Predicted Emotion")
        plt.tight_layout()
        plt.savefig(output_dir / "confusion_matrix.png", dpi=150)
        plt.close()

        # Save predictions CSV
        pred_df = filtered_df[["filename", "emotion", "canonical_emotion"]].copy()
        pred_df["predicted_canonical"] = [shared_canonical[p] for p in all_preds]
        pred_df["correct"] = (all_preds == all_targets)
        pred_df.to_csv(output_dir / "predictions.csv", index=False)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-Corpus SER Evaluation Benchmark")
    parser.add_argument("--model_ckpt", required=True, type=str, help="Path to checkpoint (model.pt) or output directory")
    parser.add_argument("--source_dataset", type=str, default=None, help="Source dataset name (e.g. cremad, ravdess, savee, tess)")
    parser.add_argument("--target_datasets", nargs="+", default=["ravdess", "savee", "tess"], help="Target dataset(s) to evaluate on, or 'all'")
    parser.add_argument("--target_split", type=str, default="test", choices=["test", "validation", "train", "full"], help="Target split")
    parser.add_argument("--output_root", type=str, default=None, help="Root directory for saving evaluation reports")
    args = parser.parse_args()

    model_ckpt = Path(args.model_ckpt).resolve()
    model, cfg, source_label_mapping = resolve_model_and_config(model_ckpt)

    # Infer source dataset name
    source_name = args.source_dataset
    if not source_name:
        for dname in DATASET_LABEL_MAPPINGS.keys():
            if f"/{dname}/" in str(model_ckpt) or f"/{dname}_" in str(model_ckpt):
                source_name = dname
                break
        if not source_name:
            source_name = "cremad"

    # Resolve target datasets
    all_datasets = ["cremad", "ravdess", "savee", "tess"]
    if "all" in args.target_datasets:
        targets = [d for d in all_datasets if d != source_name]
    else:
        targets = [d for d in args.target_datasets if d != source_name]

    model_tag = model_ckpt.parent.name if model_ckpt.is_file() else model_ckpt.name
    output_root = (
        Path(args.output_root).resolve()
        if args.output_root
        else (PROJECT_ROOT / "outputs" / "cross_corpus" / f"{source_name}_{model_tag}").resolve()
    )
    output_root.mkdir(parents=True, exist_ok=True)

    logger.info("==================================================")
    logger.info("Cross-Corpus Evaluation Benchmark")
    logger.info("Source Model:     %s (%s)", model_tag, source_name.upper())
    logger.info("Target Datasets:  %s", [t.upper() for t in targets])
    logger.info("Target Split:     %s", args.target_split)
    logger.info("Output Directory: %s", output_root)
    logger.info("==================================================")

    results = []
    for target_name in targets:
        try:
            target_out_dir = output_root / f"to_{target_name}"
            res = evaluate_single_corpus(
                model=model,
                cfg=cfg,
                source_label_mapping=source_label_mapping,
                source_name=source_name,
                target_name=target_name,
                target_split=args.target_split,
                output_dir=target_out_dir,
            )
            results.append(res)
            logger.info("-> [%s -> %s]: Accuracy=%.2f%% | Macro-F1=%.4f | UAR=%.2f%%",
                        source_name.upper(), target_name.upper(),
                        res["accuracy"] * 100, res["macro_f1"], res["uar"] * 100)
        except Exception as exc:
            logger.exception("Failed evaluation on %s: %s", target_name, exc)

    if results:
        summary_df = pd.DataFrame(results)
        summary_df.to_csv(output_root / "cross_corpus_summary.csv", index=False)
        print("\n=================== CROSS-CORPUS SUMMARY ===================")
        print(summary_df[["source_dataset", "target_dataset", "num_shared_classes", "accuracy", "macro_f1", "uar"]].to_string(index=False))
        print("============================================================\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
