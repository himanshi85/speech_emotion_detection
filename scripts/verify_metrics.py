#!/usr/bin/env python3
"""Audit per-model and combined metric artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd

from ser.core.paths import ALL_MODEL_KEYS, COMPARISON_DIR, OUTPUTS_ROOT

PER_MODEL_METRICS = (
    "training_history.csv",
    "final_results.csv",
    "computational_metrics.csv",
    "model_info.txt",
    "loss_curve.png",
    "macro_f1_curve.png",
    "accuracy_curve.png",
)

PER_MODEL_CHECKPOINTS = (
    "checkpoints/best_model/model.pt",
    "checkpoints/best_model/label_mapping.json",
    "checkpoints/final_model/model.pt",
)

PER_SPLIT_FILES = (
    "predictions.csv",
    "classification_report.csv",
    "confusion_matrix.csv",
    "confusion_matrix.png",
)

SPLITS = ("train", "validation", "test")

HISTORY_COLS = (
    "epoch",
    "train_loss",
    "train_accuracy",
    "train_macro_f1",
    "val_loss",
    "val_accuracy",
    "val_macro_f1",
)

FINAL_COLS = (
    "accuracy",
    "macro_f1",
    "macro_precision",
    "macro_recall",
    "weighted_f1",
    "uar",
    "war",
    "parameters",
    "best_val_macro_f1",
)

REPORT_EMOTIONS = 8  # per-class rows before macro/weighted avg

COMBINED_FILES = (
    "all_models_results.csv",
    "ranking_by_macro_f1.csv",
    "ranking_by_accuracy.csv",
    "tables/metrics_comparison.csv",
    "tables/per_class_f1_comparison.csv",
    "tables/train_val_test_macro_f1.csv",
    "tables/train_val_test_accuracy.csv",
    "curves/all_models_val_macro_f1.png",
    "curves/all_models_val_loss.png",
    "curves/all_models_val_accuracy.png",
    "curves/all_models_test_macro_f1_bar.png",
    "curves/all_models_test_accuracy_bar.png",
)


def _exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def audit_model(key: str, dataset_root: Path, expected_emotions: list[str]) -> tuple[bool, list[str], list[str]]:
    root = dataset_root / key
    ok_notes: list[str] = []
    issues: list[str] = []

    if not root.exists():
        return False, [], [f"{key}: no output directory"]

    trained = _exists(root / "metrics" / "final_results.csv")
    if not trained:
        issues.append(f"{key}: not trained (missing final_results.csv)")
        return False, ok_notes, issues

    for rel in PER_MODEL_METRICS:
        p = root / "metrics" / rel
        if not _exists(p):
            issues.append(f"{key}: missing metrics/{rel}")

    for rel in PER_MODEL_CHECKPOINTS:
        p = root / rel
        if not _exists(p):
            issues.append(f"{key}: missing {rel}")

    hist_path = root / "metrics" / "training_history.csv"
    if _exists(hist_path):
        hist = pd.read_csv(hist_path)
        missing_cols = [c for c in HISTORY_COLS if c not in hist.columns]
        if missing_cols:
            issues.append(f"{key}: training_history missing columns: {missing_cols}")
        else:
            ok_notes.append(f"{key}: history {len(hist)} epochs")

    final_path = root / "metrics" / "final_results.csv"
    if _exists(final_path):
        final = pd.read_csv(final_path)
        missing_cols = [c for c in FINAL_COLS if c not in final.columns]
        if missing_cols:
            issues.append(f"{key}: final_results missing columns: {missing_cols}")
        else:
            row = final.iloc[0]
            ok_notes.append(
                f"{key}: test acc={row['accuracy']:.4f} macro_f1={row['macro_f1']:.4f}"
            )

    for split in SPLITS:
        split_dir = root / "predictions" / split
        for fname in PER_SPLIT_FILES:
            p = split_dir / fname
            if not _exists(p):
                issues.append(f"{key}: missing predictions/{split}/{fname}")
        rep = split_dir / "classification_report.csv"
        if _exists(rep):
            df = pd.read_csv(rep)
            n_emotions = len(df[df["emotion"].isin(expected_emotions)])
            if n_emotions != len(expected_emotions):
                issues.append(
                    f"{key}: {split} classification_report has {n_emotions} emotions, expected {len(expected_emotions)}"
                )
            if "macro avg" not in df["emotion"].values:
                issues.append(f"{key}: {split} classification_report missing macro avg")

    return len(issues) == 0, ok_notes, issues


def audit_combined(trained_keys: list[str], comp_dir: Path) -> tuple[list[str], list[str]]:
    ok_notes: list[str] = []
    issues: list[str] = []

    if not trained_keys:
        issues.append("No trained models — combined outputs incomplete")
        return ok_notes, issues

    for rel in COMBINED_FILES:
        p = comp_dir / rel
        if not _exists(p):
            issues.append(f"comparison: missing {rel}")

    for key in trained_keys:
        cm = comp_dir / "confusion_matrices" / f"test_{key}.png"
        if not _exists(cm):
            issues.append(f"comparison: missing confusion_matrices/test_{key}.png")

    if _exists(comp_dir / "all_models_results.csv"):
        df = pd.read_csv(comp_dir / "all_models_results.csv")
        if len(df) != len(trained_keys):
            issues.append(
                f"comparison: all_models_results has {len(df)} rows, expected {len(trained_keys)}"
            )
        else:
            ok_notes.append(f"comparison: {len(df)} models in all_models_results.csv")

    return ok_notes, issues


def main() -> int:
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Audit per-model and combined metric artifacts")
    parser.add_argument("--dataset", type=str, default="ravdess", help="Dataset name (e.g. ravdess, cremad)")
    parser.add_argument("--outputs_root", type=str, default=None, help="Root folder of model outputs")
    args = parser.parse_args()

    outputs_root = Path(args.outputs_root).resolve() if args.outputs_root else OUTPUTS_ROOT / args.dataset
    comp_dir = outputs_root / "comparison"

    print(f"SER Metrics & Artifacts Audit: {args.dataset.upper()}")
    print(f"Directory: {outputs_root}")
    print("=" * 72)

    # Resolve expected emotions
    labels_file = PROJECT_ROOT / "data" / args.dataset / "metadata" / "labels.json"
    if not labels_file.exists():
        labels_file = PROJECT_ROOT / f"{args.dataset}_preprocessed" / "metadata" / "labels.json"
    if labels_file.exists():
        expected_emotions = list(json.loads(labels_file.read_text(encoding="utf-8")).keys())
    else:
        from xlsr.data.labels import CLASS_NAMES
        expected_emotions = list(CLASS_NAMES)

    trained: list[str] = []
    all_ok_notes: list[str] = []
    all_issues: list[str] = []

    for key in ALL_MODEL_KEYS:
        ok, notes, issues = audit_model(key, outputs_root, expected_emotions)
        if ok:
            trained.append(key)
        all_ok_notes.extend(notes)
        all_issues.extend(issues)

    comb_ok, comb_issues = audit_combined(trained, comp_dir)
    all_ok_notes.extend(comb_ok)
    all_issues.extend(comb_issues)

    print("\nPer-model status:")
    for key in ALL_MODEL_KEYS:
        final = outputs_root / key / "metrics" / "final_results.csv"
        status = "COMPLETE" if key in trained else "NOT TRAINED"
        print(f"  {key:<22} {status}")

    if all_ok_notes:
        print("\nVerified:")
        for n in all_ok_notes:
            print(f"  + {n}")

    if all_issues:
        print("\nIssues:")
        for i in all_issues:
            print(f"  - {i}")
    else:
        print("\nAll metrics, graphs, and reports stored correctly.")

    print(f"\nExpected per trained model in {outputs_root}:")
    print("  metrics/     training_history.csv, final_results.csv, 3 curve PNGs")
    print("  predictions/ train|validation|test -> predictions, report, CM csv+png")
    print("  checkpoints/ best_model + final_model")
    print(f"\nExpected combined ({comp_dir}):")
    print("  CSV tables, ranking, per-class F1, train/val/test accuracy+F1")
    print("  Curves: val macro-F1, val loss, val accuracy, test bar charts")
    print("  confusion_matrices/test_<model>.png")

    report_path = comp_dir / "metrics_audit.txt"
    comp_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"Dataset: {args.dataset}", f"Trained: {len(trained)}/{len(ALL_MODEL_KEYS)}", ""]
    lines.extend(all_ok_notes)
    lines.extend(all_issues)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved: {report_path}")

    return 0 if not all_issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
