"""Paths for multi-model SER experiments."""

from __future__ import annotations

from pathlib import Path

def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for p in [current] + list(current.parents):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
    return Path(__file__).resolve().parents[3]

PROJECT_ROOT = _find_project_root()

# Support both data/ravdess and ravdess_preprocessed
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "ravdess" if (PROJECT_ROOT / "data" / "ravdess").exists() else PROJECT_ROOT / "ravdess_preprocessed"
OUTPUTS_ROOT = PROJECT_ROOT / "outputs"
DEFAULT_OUTPUTS_ROOT = OUTPUTS_ROOT / "ravdess"
COMPARISON_DIR = OUTPUTS_ROOT / "ravdess" / "comparison"

ALL_MODEL_KEYS = (
    "mfcc_lstm",
    "mfcc_cnn_bilstm",
    "wav2vec2_xlsr_300m",
    "wav2vec2",
    "hubert",
    "wavlm",
    "emotion2vec_plus",
    "beats",
)

OUTPUT_SUBDIRS = (
    "checkpoints/best_model",
    "checkpoints/final_model",
    "metrics",
    "predictions/train",
    "predictions/validation",
    "predictions/test",
    "logs",
)


def model_output_dir(model_key: str, dataset: str = "ravdess") -> Path:
    return OUTPUTS_ROOT / dataset / model_key


def get_comparison_dir(dataset: str = "ravdess") -> Path:
    return OUTPUTS_ROOT / dataset / "comparison"
