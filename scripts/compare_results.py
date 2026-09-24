#!/usr/bin/env python3
"""Merge all model results and build comparison tables + curves."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import logging

import matplotlib.pyplot as plt
import pandas as pd

from ser.core.paths import ALL_MODEL_KEYS, COMPARISON_DIR, OUTPUTS_ROOT
from xlsr.data.labels import CLASS_NAMES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("compare_results")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Merge all model results and build comparison tables + curves")
    parser.add_argument("--outputs_root", type=str, default=None, help="Root directory containing model output folders (e.g. outputs/ravdess or outputs/cremad)")
    parser.add_argument("--dataset", type=str, default="ravdess", help="Dataset name shortcut (e.g. ravdess or cremad)")
    parser.add_argument("--comparison_dir", type=str, default=None, help="Directory to save comparison outputs")
    args = parser.parse_args()

    if args.outputs_root:
        outputs_root = Path(args.outputs_root).resolve()
    else:
        outputs_root = (OUTPUTS_ROOT / args.dataset).resolve()
    comparison_dir = Path(args.comparison_dir).resolve() if args.comparison_dir else outputs_root / "comparison"

    rows = []
    histories = {}
    per_class = []

    candidate_dirs = []
    for key in ALL_MODEL_KEYS:
        d = outputs_root / key
        if d.exists() and d not in candidate_dirs:
            candidate_dirs.append(d)
    if outputs_root.exists():
        for sub in sorted(outputs_root.iterdir()):
            if sub.is_dir() and sub not in candidate_dirs and (sub / "metrics" / "final_results.csv").exists():
                candidate_dirs.append(sub)

    for model_dir in candidate_dirs:
        key = model_dir.name
        final_path = model_dir / "metrics" / "final_results.csv"
        if not final_path.exists():
            continue
        df = pd.read_csv(final_path)
        rows.append(df.iloc[0].to_dict())

        hist_path = model_dir / "metrics" / "training_history.csv"
        if hist_path.exists():
            histories[key] = pd.read_csv(hist_path)

        labels_json = model_dir / "checkpoints" / "best_model" / "label_mapping.json"
        if labels_json.exists():
            import json
            lmap = json.loads(labels_json.read_text(encoding="utf-8"))
            class_names = [k for k, v in sorted(lmap.items(), key=lambda x: x[1])]
        else:
            class_names = CLASS_NAMES

        for split in ("train", "validation", "test"):
            rep_path = model_dir / "predictions" / split / "classification_report.csv"
            if rep_path.exists():
                rep = pd.read_csv(rep_path)
                for emotion in class_names:
                    match = rep[rep["emotion"] == emotion]
                    if len(match):
                        per_class.append(
                            {
                                "model_key": key,
                                "model": df.iloc[0].get("model", key),
                                "split": split,
                                "emotion": emotion,
                                "f1_score": match.iloc[0]["f1_score"],
                            }
                        )

    if not rows:
        logger.error("No model results found under %s", outputs_root)
        return 1

    comparison_dir.mkdir(parents=True, exist_ok=True)
    (comparison_dir / "tables").mkdir(exist_ok=True)
    (comparison_dir / "curves").mkdir(exist_ok=True)
    (comparison_dir / "confusion_matrices").mkdir(exist_ok=True)

    all_df = pd.DataFrame(rows)
    all_df.to_csv(comparison_dir / "all_models_results.csv", index=False)

    rank_f1 = all_df.sort_values("macro_f1", ascending=False)
    rank_f1.to_csv(comparison_dir / "ranking_by_macro_f1.csv", index=False)
    all_df.sort_values("accuracy", ascending=False).to_csv(
        comparison_dir / "ranking_by_accuracy.csv", index=False
    )

    metric_cols = [
        "model", "accuracy", "macro_f1", "uar", "war",
        "weighted_f1", "parameters", "training_time_sec", "best_val_macro_f1",
    ]
    all_df[[c for c in metric_cols if c in all_df.columns]].to_csv(
        comparison_dir / "tables" / "metrics_comparison.csv", index=False
    )

    accuracy_rows = []
    if per_class:
        pc_df = pd.DataFrame(per_class)
        test_pc = pc_df[pc_df["split"] == "test"]
        pivot = test_pc.pivot_table(index=["model_key", "model"], columns="emotion", values="f1_score", aggfunc="first")
        pivot.to_csv(comparison_dir / "tables" / "per_class_f1_comparison.csv")

        tvt = pc_df.groupby(["model_key", "model", "split"])["f1_score"].mean().reset_index()
        tvt_pivot = tvt.pivot_table(index=["model_key", "model"], columns="split", values="f1_score", aggfunc="first")
        tvt_pivot.to_csv(comparison_dir / "tables" / "train_val_test_macro_f1.csv")

        for model_dir in candidate_dirs:
            key = model_dir.name
            model_name = None
            for split in ("train", "validation", "test"):
                rep_path = model_dir / "predictions" / split / "classification_report.csv"
                if not rep_path.exists():
                    continue
                rep = pd.read_csv(rep_path)
                wavg = rep[rep["emotion"] == "weighted avg"]
                if len(wavg):
                    if model_name is None:
                        final_path = model_dir / "metrics" / "final_results.csv"
                        model_name = (
                            pd.read_csv(final_path).iloc[0].get("model", key)
                            if final_path.exists()
                            else key
                        )
                    accuracy_rows.append(
                        {
                            "model": model_name,
                            "model_key": key,
                            "split": split,
                            "accuracy": wavg.iloc[0]["recall"],
                        }
                    )
        if accuracy_rows:
            acc_df = pd.DataFrame(accuracy_rows)
            acc_pivot = acc_df.pivot_table(index=["model_key", "model"], columns="split", values="accuracy", aggfunc="first")
            acc_pivot.to_csv(comparison_dir / "tables" / "train_val_test_accuracy.csv")

    # Val macro-F1 curves — all models
    plt.figure(figsize=(10, 6))
    for key, hist in histories.items():
        if "val_macro_f1" in hist.columns:
            plt.plot(hist["epoch"], hist["val_macro_f1"], label=key)
    plt.xlabel("Epoch")
    plt.ylabel("Validation Macro-F1")
    plt.title("All Models — Validation Macro-F1")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(comparison_dir / "curves" / "all_models_val_macro_f1.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 6))
    for key, hist in histories.items():
        if "val_loss" in hist.columns:
            plt.plot(hist["epoch"], hist["val_loss"], label=key)
    plt.xlabel("Epoch")
    plt.ylabel("Validation Loss")
    plt.title("All Models — Validation Loss")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(comparison_dir / "curves" / "all_models_val_loss.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 6))
    for key, hist in histories.items():
        if "val_accuracy" in hist.columns:
            plt.plot(hist["epoch"], hist["val_accuracy"], label=key)
    plt.xlabel("Epoch")
    plt.ylabel("Validation Accuracy")
    plt.title("All Models — Validation Accuracy")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(comparison_dir / "curves" / "all_models_val_accuracy.png", dpi=150)
    plt.close()

    # Test macro-F1 bar chart
    plt.figure(figsize=(10, 5))
    plt.bar(all_df["model"], all_df["macro_f1"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Test Macro-F1")
    plt.title("All Models — Test Macro-F1")
    plt.tight_layout()
    plt.savefig(comparison_dir / "curves" / "all_models_test_macro_f1_bar.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.bar(all_df["model"], all_df["accuracy"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Test Accuracy")
    plt.title("All Models — Test Accuracy")
    plt.tight_layout()
    plt.savefig(comparison_dir / "curves" / "all_models_test_accuracy_bar.png", dpi=150)
    plt.close()

    # Copy test confusion matrices
    for key in ALL_MODEL_KEYS:
        src = outputs_root / key / "predictions" / "test" / "confusion_matrix.png"
        if src.exists():
            import shutil
            shutil.copy(src, comparison_dir / "confusion_matrices" / f"test_{key}.png")

    logger.info("Comparison written to %s", comparison_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
