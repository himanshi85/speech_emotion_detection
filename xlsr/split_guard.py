"""
Section 3 — Actor-independent split guard.

Uses the preprocessing split exactly:
  Train: actors 01–16
  Validation: actors 17–20
  Test: actors 21–24

Never moves actors between splits.
If leakage is detected, execution must stop.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from xlsr.dataset_io import (
    EXPECTED_TEST_ACTORS,
    EXPECTED_TRAIN_ACTORS,
    EXPECTED_VAL_ACTORS,
    DatasetBundle,
    get_actor_sets,
    load_ravdess_splits,
)
from xlsr.experiment_dirs import create_experiment_dirs
from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR

logger = logging.getLogger(__name__)


class ActorLeakageError(RuntimeError):
    """Raised when actor leakage or split mismatch is detected. Stops training."""


@dataclass
class SplitVerificationReport:
    ok: bool
    train_actors: Set[int]
    validation_actors: Set[int]
    test_actors: Set[int]
    intersections: Dict[str, List[int]]
    issues: List[str] = field(default_factory=list)
    sizes: Dict[str, int] = field(default_factory=dict)

    def to_text(self) -> str:
        status = "PASSED" if self.ok else "FAILED — STOP EXECUTION"
        lines = [
            "RAVDESS Actor-Independent Split Verification (Section 3)",
            "=" * 60,
            f"Status: {status}",
            "",
            "Required split (must not be changed):",
            f"  Train actors:      {sorted(EXPECTED_TRAIN_ACTORS)}",
            f"  Validation actors: {sorted(EXPECTED_VAL_ACTORS)}",
            f"  Test actors:       {sorted(EXPECTED_TEST_ACTORS)}",
            "",
            "Observed actors:",
            f"  Train:      {sorted(self.train_actors)}",
            f"  Validation: {sorted(self.validation_actors)}",
            f"  Test:       {sorted(self.test_actors)}",
            "",
            "Leakage checks (must all be empty):",
            f"  Train ∩ Validation = {self.intersections['train_validation']}",
            f"  Train ∩ Test       = {self.intersections['train_test']}",
            f"  Validation ∩ Test  = {self.intersections['validation_test']}",
            "",
            f"Sizes: {self.sizes}",
        ]
        if self.issues:
            lines.append("")
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")
        else:
            lines.append("")
            lines.append("No actor leakage detected. Actor-independent split preserved.")
        return "\n".join(lines) + "\n"


def _check_row_level_actor_split(bundle: DatasetBundle) -> List[str]:
    """Ensure every row's actor_id matches the file's declared split assignment."""
    issues: List[str] = []
    mapping = {
        "train": EXPECTED_TRAIN_ACTORS,
        "validation": EXPECTED_VAL_ACTORS,
        "test": EXPECTED_TEST_ACTORS,
    }
    for split_name, expected_actors in mapping.items():
        df = getattr(bundle, split_name if split_name != "validation" else "validation")
        # getattr: train, validation, test
        if split_name == "train":
            df = bundle.train
        elif split_name == "validation":
            df = bundle.validation
        else:
            df = bundle.test

        wrong = df[~df["actor_id"].isin(expected_actors)]
        if len(wrong):
            bad = (
                wrong.groupby("actor_id").size().to_dict()
            )
            issues.append(
                f"{split_name}.csv contains actors outside allowed set: {bad}"
            )

        # Any actor appearing with a different split label inside this CSV
        if not (df["split"] == split_name).all():
            issues.append(
                f"{split_name}.csv has rows whose split column != '{split_name}'"
            )
    return issues


def _check_actor_appears_in_one_split_only(bundle: DatasetBundle) -> List[str]:
    """Every actor_id must appear in exactly one of train/validation/test."""
    issues: List[str] = []
    membership: Dict[int, List[str]] = {}
    for split_name, df in (
        ("train", bundle.train),
        ("validation", bundle.validation),
        ("test", bundle.test),
    ):
        for actor_id in df["actor_id"].unique():
            actor_id = int(actor_id)
            membership.setdefault(actor_id, []).append(split_name)

    for actor_id, splits in sorted(membership.items()):
        if len(splits) > 1:
            issues.append(
                f"Actor {actor_id:02d} appears in multiple splits: {splits}"
            )
    return issues


def verify_dataset_split(bundle: DatasetBundle) -> SplitVerificationReport:
    """
    Run full Section 3 checks. Does not raise; returns a report.
    """
    actors = get_actor_sets(bundle)
    train_a = actors["train"]
    val_a = actors["validation"]
    test_a = actors["test"]

    intersections = {
        "train_validation": sorted(train_a & val_a),
        "train_test": sorted(train_a & test_a),
        "validation_test": sorted(val_a & test_a),
    }

    issues: List[str] = []

    if intersections["train_validation"]:
        issues.append(
            f"Train actors ∩ Validation actors = {intersections['train_validation']}"
        )
    if intersections["train_test"]:
        issues.append(
            f"Train actors ∩ Test actors = {intersections['train_test']}"
        )
    if intersections["validation_test"]:
        issues.append(
            f"Validation actors ∩ Test actors = {intersections['validation_test']}"
        )

    if train_a != EXPECTED_TRAIN_ACTORS:
        issues.append(
            f"Train actors must be exactly {sorted(EXPECTED_TRAIN_ACTORS)}; "
            f"got {sorted(train_a)}"
        )
    if val_a != EXPECTED_VAL_ACTORS:
        issues.append(
            f"Validation actors must be exactly {sorted(EXPECTED_VAL_ACTORS)}; "
            f"got {sorted(val_a)}"
        )
    if test_a != EXPECTED_TEST_ACTORS:
        issues.append(
            f"Test actors must be exactly {sorted(EXPECTED_TEST_ACTORS)}; "
            f"got {sorted(test_a)}"
        )

    issues.extend(_check_row_level_actor_split(bundle))
    issues.extend(_check_actor_appears_in_one_split_only(bundle))

    return SplitVerificationReport(
        ok=len(issues) == 0,
        train_actors=train_a,
        validation_actors=val_a,
        test_actors=test_a,
        intersections=intersections,
        issues=issues,
        sizes=bundle.sizes,
    )


def assert_no_actor_leakage(bundle: DatasetBundle) -> SplitVerificationReport:
    """
    Hard gate before training.

    If leakage / split mismatch is found: raise ActorLeakageError and stop.
    """
    report = verify_dataset_split(bundle)
    if not report.ok:
        message = (
            "ACTOR LEAKAGE / SPLIT FAILURE — stopping execution.\n"
            + "\n".join(f"  - {i}" for i in report.issues)
        )
        logger.error(message)
        raise ActorLeakageError(message)

    logger.info("Actor leakage checks passed (train∩val∩test empty; fixed actor sets OK)")
    return report


def run_split_guard(
    data_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    stop_on_failure: bool = True,
) -> SplitVerificationReport:
    """
    Load existing splits, verify actor independence, write report under outputs/.

    Training must call this (or assert_no_actor_leakage) before starting.
    """
    data_root = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    out_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR

    exp = create_experiment_dirs(out_root)
    bundle = load_ravdess_splits(data_root)
    report = verify_dataset_split(bundle)

    report_path = exp["metrics"] / "split_verification.txt"
    report_path.write_text(report.to_text(), encoding="utf-8")
    logger.info("Split verification report written: %s", report_path)

    if stop_on_failure and not report.ok:
        raise ActorLeakageError(
            "ACTOR LEAKAGE / SPLIT FAILURE — stopping execution.\n"
            + "\n".join(f"  - {i}" for i in report.issues)
            + f"\nSee report: {report_path}"
        )

    return report
