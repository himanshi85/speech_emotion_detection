"""Unit tests for Multi-Corpus Combined Dataset Preprocessing."""

from pathlib import Path
import pytest
from xlsr.data.dataset import load_ravdess_splits

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_combined_splits_exist():
    combined_dir = PROJECT_ROOT / "data" / "combined" if (PROJECT_ROOT / "data" / "combined").exists() else PROJECT_ROOT / "combined_preprocessed"
    if not combined_dir.exists():
        pytest.skip("combined dataset does not exist yet")

    bundle = load_ravdess_splits(combined_dir)
    assert bundle.sizes["train"] > 7000
    assert bundle.sizes["validation"] > 1500
    assert bundle.sizes["test"] > 1500
    assert bundle.sizes["total"] > 11000


def test_combined_classes_are_canonical_six():
    combined_dir = PROJECT_ROOT / "data" / "combined" if (PROJECT_ROOT / "data" / "combined").exists() else PROJECT_ROOT / "combined_preprocessed"
    if not combined_dir.exists():
        pytest.skip("combined dataset does not exist yet")

    bundle = load_ravdess_splits(combined_dir)
    emotions = set(bundle.train["emotion"].unique())
    expected = {"angry", "disgust", "fear", "happy", "neutral", "sad"}
    assert emotions == expected


def test_audio_files_resolve():
    combined_dir = PROJECT_ROOT / "data" / "combined" if (PROJECT_ROOT / "data" / "combined").exists() else PROJECT_ROOT / "combined_preprocessed"
    if not combined_dir.exists():
        pytest.skip("combined dataset does not exist yet")

    bundle = load_ravdess_splits(combined_dir)
    # Test first 5 files from each split
    for split_df in [bundle.train, bundle.validation, bundle.test]:
        for _, row in split_df.head(5).iterrows():
            abs_path = (bundle.data_dir / row["filepath"]).resolve()
            assert abs_path.exists(), f"Audio file not found: {abs_path}"
