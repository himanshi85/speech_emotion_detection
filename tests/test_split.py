"""Unit tests for actor-independent split validation."""

from __future__ import annotations

from ser.data.dataset import load_ravdess_splits
from ser.data.split import verify_dataset_split


def test_no_actor_leakage_in_preprocessed_dataset() -> None:
    bundle = load_ravdess_splits()
    report = verify_dataset_split(bundle)
    assert report.ok
    assert report.intersections["train_validation"] == []
    assert report.intersections["train_test"] == []
    assert report.intersections["validation_test"] == []


def test_no_word_leakage_in_tess() -> None:
    from pathlib import Path
    tess_dir = Path("data/tess") if Path("data/tess").exists() else Path("tess_preprocessed")
    if not tess_dir.exists():
        return
    bundle = load_ravdess_splits(tess_dir)
    report = verify_dataset_split(bundle)
    assert report.ok
    assert report.intersections["train_validation"] == []
    assert report.intersections["train_test"] == []
    assert report.intersections["validation_test"] == []

