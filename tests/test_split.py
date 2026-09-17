"""Unit tests for actor-independent split validation."""

from __future__ import annotations

from xlsr.data.dataset import load_ravdess_splits
from xlsr.data.split import verify_dataset_split


def test_no_actor_leakage_in_preprocessed_dataset() -> None:
    bundle = load_ravdess_splits()
    report = verify_dataset_split(bundle)
    assert report.ok
    assert report.intersections["train_validation"] == []
    assert report.intersections["train_test"] == []
    assert report.intersections["validation_test"] == []
