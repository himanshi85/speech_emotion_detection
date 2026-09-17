#!/usr/bin/env python3
"""Merge all model results and build comparison tables + curves."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging

import matplotlib.pyplot as plt
import pandas as pd

from ser.core.paths import ALL_MODEL_KEYS, COMPARISON_DIR, OUTPUTS_ROOT
from xlsr.data.labels import CLASS_NAMES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("compare_results")


def main() -> int:
    rows = []
    histories = {}
    per_class = []

    for key in ALL_MODEL_KEYS:
        final_path = OUTPUTS_ROOT / key / "metrics" / "final_results.csv"
        if not final_path.exists():
            logger.warning("Missing results for %s", key)
            continue
        df = pd.read_csv(final_path)
        rows.append(df.iloc[0].to_dict())

        hist_path = OUTPUTS_ROOT / key / "metrics" / "training_history.csv"
        if hist_path.exists():
            histories[key] = pd.read_csv(hist_path)

        for split in ("train", "validation", "test"):
            rep_path = OUTPUTS_ROOT / key / "predictions" / split / "classification_report.csv"
            if rep_path.exists():
                rep = pd.read_csv(rep_path)
                for emotion in CLASS_NAMES:
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
        logger.error("No model results found under %s", OUTPUTS_ROOT)
        return 1

    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    (COMPARISON_DIR / "tables").mkdir(exist_ok=True)
    (COMPARISON_DIR / "curves").mkdir(exist_ok=True)
    (COMPARISON_DIR / "confusion_matrices").mkdir(exist_ok=True)

    all_df = pd.DataFrame(rows)
    all_df.to_csv(COMPARISON_DIR / "all_models_results.csv", index=False)

    rank_f1 = all_df.sort_values("macro_f1", ascending=False)
    rank_f1.to_csv(COMPARISON_DIR / "ranking_by_macro_f1.csv", index=False)
    all_df.sort_values("accuracy", ascending=False).to_csv(
        COMPARISON_DIR / "ranking_by_accuracy.csv", index=False
    )

    metric_cols = [
        "model", "accuracy", "macro_f1", "uar", "war",
        "weighted_f1", "parameters", "training_time_sec", "best_val_macro_f1",
    ]
    all_df[[c for c in metric_cols if c in all_df.columns]].to_csv(
        COMPARISON_DIR / "tables" / "metrics_comparison.csv", index=False
    )

    accuracy_rows = []
    if per_class:
        pc_df = pd.DataFrame(per_class)
        test_pc = pc_df[pc_df["split"] == "test"]
        pivot = test_pc.pivot(index="model", columns="emotion", values="f1_score")
        pivot.to_csv(COMPARISON_DIR / "tables" / "per_class_f1_comparison.csv")

        tvt = pc_df.groupby(["model", "split"])["f1_score"].mean().reset_index()
        tvt_pivot = tvt.pivot(index="model", columns="split", values="f1_score")
        tvt_pivot.to_csv(COMPARISON_DIR / "tables" / "train_val_test_macro_f1.csv")

        for key in ALL_MODEL_KEYS:
            model_name = None
            for split in ("train", "validation", "test"):
                rep_path = OUTPUTS_ROOT / key / "predictions" / split / "classification_report.csv"
                if not rep_path.exists():
                    continue
                rep = pd.read_csv(rep_path)
                wavg = rep[rep["emotion"] == "weighted avg"]
                if len(wavg):
                    if model_name is None:
                        final_path = OUTPUTS_ROOT / key / "metrics" / "final_results.csv"
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
            acc_pivot = acc_df.pivot(index="model", columns="split", values="accuracy")
            acc_pivot.to_csv(COMPARISON_DIR / "tables" / "train_val_test_accuracy.csv")

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
    plt.savefig(COMPARISON_DIR / "curves" / "all_models_val_macro_f1.png", dpi=150)
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
    plt.savefig(COMPARISON_DIR / "curves" / "all_models_val_loss.png", dpi=150)
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
    plt.savefig(COMPARISON_DIR / "curves" / "all_models_val_accuracy.png", dpi=150)
    plt.close()

    # Test macro-F1 bar chart
    plt.figure(figsize=(10, 5))
    plt.bar(all_df["model"], all_df["macro_f1"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Test Macro-F1")
    plt.title("All Models — Test Macro-F1")
    plt.tight_layout()
    plt.savefig(COMPARISON_DIR / "curves" / "all_models_test_macro_f1_bar.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.bar(all_df["model"], all_df["accuracy"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Test Accuracy")
    plt.title("All Models — Test Accuracy")
    plt.tight_layout()
    plt.savefig(COMPARISON_DIR / "curves" / "all_models_test_accuracy_bar.png", dpi=150)
    plt.close()

    # Copy test confusion matrices
    for key in ALL_MODEL_KEYS:
        src = OUTPUTS_ROOT / key / "predictions" / "test" / "confusion_matrix.png"
        if src.exists():
            import shutil
            shutil.copy(src, COMPARISON_DIR / "confusion_matrices" / f"test_{key}.png")

    logger.info("Comparison written to %s", COMPARISON_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
