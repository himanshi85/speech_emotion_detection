"""
Actor-independent split guard.

Train: actors 01–16 | Validation: 17–20 | Test: 21–24
Never move actors between splits.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set

from xlsr.data.dataset import (
    EXPECTED_TEST_ACTORS,
    EXPECTED_TRAIN_ACTORS,
    EXPECTED_VAL_ACTORS,
    DatasetBundle,
    get_actor_sets,
)

logger = logging.getLogger(__name__)


class ActorLeakageError(RuntimeError):
    """Raised when actor leakage or split mismatch is detected."""


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
    issues: List[str] = []
    all_actors = set(bundle.train["actor_id"]).union(bundle.validation["actor_id"]).union(bundle.test["actor_id"])
    is_ravdess = "ravdess" in bundle.data_dir.name.lower() and all_actors.issubset(set(range(1, 25)))

    if is_ravdess:
        mapping = {
            "train": (bundle.train, EXPECTED_TRAIN_ACTORS),
            "validation": (bundle.validation, EXPECTED_VAL_ACTORS),
            "test": (bundle.test, EXPECTED_TEST_ACTORS),
        }
        for split_name, (df, expected_actors) in mapping.items():
            wrong = df[~df["actor_id"].isin(expected_actors)]
            if len(wrong):
                bad = wrong.groupby("actor_id").size().to_dict()
                issues.append(
                    f"{split_name}.csv contains actors outside allowed set: {bad}"
                )

    for split_name, df in (("train", bundle.train), ("validation", bundle.validation), ("test", bundle.test)):
        if not (df["split"] == split_name).all():
            issues.append(
                f"{split_name}.csv has rows whose split column != '{split_name}'"
            )
    return issues


def _check_actor_appears_in_one_split_only(bundle: DatasetBundle) -> List[str]:
    issues: List[str] = []
    membership: Dict[int, List[str]] = {}
    for split_name, df in (
        ("train", bundle.train),
        ("validation", bundle.validation),
        ("test", bundle.test),
    ):
        for actor_id in df["actor_id"].unique():
            membership.setdefault(int(actor_id), []).append(split_name)

    for actor_id, splits in sorted(membership.items()):
        if len(splits) > 1:
            issues.append(
                f"Actor {actor_id:02d} appears in multiple splits: {splits}"
            )
    return issues


def verify_dataset_split(bundle: DatasetBundle) -> SplitVerificationReport:
    """Run full Section 3 checks. Does not raise; returns a report."""
    actors = get_actor_sets(bundle)
    train_a = actors["train"]
    val_a = actors["validation"]
    test_a = actors["test"]

    is_tess = "tess" in bundle.data_dir.name.lower()
    if is_tess:
        train_words = set(bundle.train["word"]) if "word" in bundle.train.columns else set()
        val_words = set(bundle.validation["word"]) if "word" in bundle.validation.columns else set()
        test_words = set(bundle.test["word"]) if "word" in bundle.test.columns else set()
        intersections = {
            "train_validation": sorted(train_words & val_words),
            "train_test": sorted(train_words & test_words),
            "validation_test": sorted(val_words & test_words),
        }
        issues: List[str] = []
        if intersections["train_validation"]:
            issues.append(f"Prompt/word leakage: Train words ∩ Validation words = {intersections['train_validation'][:5]}")
        if intersections["train_test"]:
            issues.append(f"Prompt/word leakage: Train words ∩ Test words = {intersections['train_test'][:5]}")
        if intersections["validation_test"]:
            issues.append(f"Prompt/word leakage: Validation words ∩ Test words = {intersections['validation_test'][:5]}")
        issues.extend(_check_row_level_actor_split(bundle))
        return SplitVerificationReport(
            ok=len(issues) == 0,
            train_actors=train_a,
            validation_actors=val_a,
            test_actors=test_a,
            intersections=intersections,
            issues=issues,
            sizes=bundle.sizes,
        )

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

    all_actors = train_a.union(val_a).union(test_a)
    is_ravdess = "ravdess" in bundle.data_dir.name.lower() and all_actors.issubset(set(range(1, 25)))

    if is_ravdess:
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
    """Hard gate before training. Raises ActorLeakageError on failure."""
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
