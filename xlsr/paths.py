"""
Default paths for the XLS-R SER experiment.

Data: existing ravdess_preprocessed/ (do not re-split).
Results: outputs/wav2vec2_xlsr_300m/ (all training artifacts).
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Existing preprocessed RAVDESS dataset (Section 2)
DEFAULT_DATA_DIR = PROJECT_ROOT / "ravdess_preprocessed"

# All training / evaluation results go here (Section 34)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "wav2vec2_xlsr_300m"

METADATA_SUBDIR = "metadata"
AUDIO_SUBDIR = "audio"

TRAIN_CSV_NAME = "train.csv"
VALIDATION_CSV_NAME = "validation.csv"
TEST_CSV_NAME = "test.csv"
FULL_METADATA_CSV_NAME = "ravdess_metadata.csv"

# Experiment output subfolders
OUTPUT_SUBDIRS = (
    "checkpoints/best_model",
    "checkpoints/final_model",
    "metrics",
    "predictions",
    "logs",
)
