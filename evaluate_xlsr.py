"""
CLI Evaluation Script for Wav2Vec2-XLS-R-300M SER.

Section 35:
python evaluate_xlsr.py \
    --checkpoint outputs/wav2vec2_xlsr_300m/checkpoints/best_model \
    --test_csv ravdess_preprocessed/metadata/test.csv
"""

from __future__ import annotations

import argparse
import logging
import time
import sys
from pathlib import Path

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import pandas as pd
import torch
from torch.utils.data import DataLoader

from xlsr.constants import MODEL_NAME, NUM_CLASSES
from xlsr.dataset import RAVDESSXLSRDataset, SERDataCollator
from xlsr.dataset_io import _load_split_csv
from xlsr.experiment_dirs import create_experiment_dirs
from xlsr.metrics import (
    compute_ser_metrics,
    save_classification_report,
    save_confusion_matrix,
    save_test_predictions,
)
from xlsr.model import Wav2Vec2XLSRForSER, build_xlsr_ser_model
from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.processor import get_xlsr_processor

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Wav2Vec2-XLS-R-300M SER Checkpoint on Test Set")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to checkpoint directory (best_model)")
    parser.add_argument("--test_csv", type=str, default=None, help="Path to test.csv (defaults to ravdess_preprocessed/metadata/test.csv)")
    parser.add_argument("--data_dir", type=str, default=str(DEFAULT_DATA_DIR), help="Path to preprocessed RAVDESS dataset root")
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory for predictions and metrics")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size for evaluation")
    return parser.parse_args()


def load_model_from_checkpoint(checkpoint_dir: Path, device: torch.device) -> Wav2Vec2XLSRForSER:
    """Load model from saved checkpoint directory (Section 22, 24)."""
    checkpoint_dir = Path(checkpoint_dir).resolve()
    ckpt_file = checkpoint_dir / "model_checkpoint.pt"

    if not ckpt_file.exists():
        raise FileNotFoundError(f"Checkpoint file missing: {ckpt_file}")

    state = torch.load(ckpt_file, map_location=device)
    config = state.get("config", {})
    dropout = float(config.get("dropout", 0.3))

    model = build_xlsr_ser_model(
        model_name=MODEL_NAME,
        num_classes=NUM_CLASSES,
        dropout=dropout,
        freeze_encoder=False,
    )
    model.load_state_dict(state["model_state_dict"])
    model.to(device)
    model.eval()
    logger.info("Successfully loaded checkpoint from %s (Epoch %d)", checkpoint_dir, state.get("epoch", -1))
    return model


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    dirs = create_experiment_dirs(output_dir)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting Test Evaluation")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = Path(args.data_dir).resolve()
    test_csv_path = Path(args.test_csv).resolve() if args.test_csv else data_dir / "metadata" / "test.csv"

    if not test_csv_path.exists():
        raise FileNotFoundError(f"Test CSV not found: {test_csv_path}")

    # Load test split CSV
    test_df = _load_split_csv(test_csv_path, "test", data_dir)
    logger.info("Loaded %d test samples from %s", len(test_df), test_csv_path)

    # Load model and processor
    model = load_model_from_checkpoint(Path(args.checkpoint), device)
    processor = get_xlsr_processor(model_name=MODEL_NAME)
    collator = SERDataCollator(processor)

    test_dataset = RAVDESSXLSRDataset(test_df, data_dir=data_dir)
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collator,
    )

    # Run inference and measure timing (Section 31)
    all_preds = []
    all_labels = []
    all_probs = []

    start_infer_time = time.time()
    with torch.no_grad():
        for batch in test_loader:
            input_values = batch["input_values"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_values=input_values, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
            preds = torch.argmax(outputs.logits, dim=-1).cpu().numpy()

            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs)

    total_inference_time = time.time() - start_infer_time
    avg_inference_per_file = total_inference_time / len(test_dataset) if len(test_dataset) > 0 else 0.0

    # Calculate evaluation metrics (Section 24, 25)
    metrics = compute_ser_metrics(all_labels, all_preds)
    all_probs_arr = torch.tensor(all_probs).numpy() if len(all_probs) > 0 else None

    # Save artifacts (Section 26, 27, 28)
    save_confusion_matrix(all_labels, all_preds, output_dir)
    save_classification_report(all_labels, all_preds, output_dir)
    save_test_predictions(test_df, all_labels, all_preds, all_probs_arr, output_dir)

    # Save computational metrics (Section 31)
    param_counts = model.count_parameters()
    comp_df = pd.DataFrame([{
        "total_test_inference_time_sec": total_inference_time,
        "avg_inference_time_per_file_sec": avg_inference_per_file,
        "num_test_files": len(test_dataset),
        "device": str(device),
        "total_parameters": param_counts["total"],
        "trainable_parameters": param_counts["trainable"],
    }])
    comp_path = dirs["metrics"] / "computational_metrics.csv"
    comp_df.to_csv(comp_path, index=False)
    logger.info("Saved computational metrics to %s", comp_path)

    # Save final results CSV (Section 32)
    final_results_df = pd.DataFrame([{
        "model": "Wav2Vec2-XLS-R-300M",
        "accuracy": metrics["accuracy"],
        "macro_precision": metrics["macro_precision"],
        "macro_recall": metrics["macro_recall"],
        "macro_f1": metrics["macro_f1"],
        "weighted_precision": metrics["weighted_precision"],
        "weighted_recall": metrics["weighted_recall"],
        "weighted_f1": metrics["weighted_f1"],
        "uar": metrics["uar"],
        "war": metrics["war"],
        "parameters": param_counts["total"],
        "trainable_parameters": param_counts["trainable"],
        "training_time": "N/A",
        "inference_time": total_inference_time,
    }])
    final_path = dirs["metrics"] / "final_results.csv"
    final_results_df.to_csv(final_path, index=False)
    logger.info("Saved final results CSV to %s", final_path)

    print("\n" + "=" * 60)
    print("Test Evaluation Complete!")
    print(f"Model: Wav2Vec2-XLS-R-300M")
    print(f"Test Accuracy (WAR): {metrics['accuracy'] * 100:.2f}%")
    print(f"Test Macro-F1:       {metrics['macro_f1']:.4f}")
    print(f"Test UAR:            {metrics['uar']:.4f}")
    print(f"Inference Time:      {total_inference_time:.2f}s ({avg_inference_per_file * 1000:.1f}ms/file)")
    print(f"Artifacts Saved To:  {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
