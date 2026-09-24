"""
Locked 8-class emotion label mapping for RAVDESS SER.

Do NOT change this mapping later. All future models in this research
comparison must use the same IDs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List

import pandas as pd

if TYPE_CHECKING:
    from xlsr.data.dataset import DatasetBundle

logger = logging.getLogger(__name__)

NUM_CLASSES = 8

EMOTION_TO_ID: Dict[str, int] = {
    "neutral": 0,
    "calm": 1,
    "happy": 2,
    "sad": 3,
    "angry": 4,
    "fearful": 5,
    "disgust": 6,
    "surprised": 7,
}

ID_TO_EMOTION: Dict[int, str] = {
    0: "neutral",
    1: "calm",
    2: "happy",
    3: "sad",
    4: "angry",
    5: "fearful",
    6: "disgust",
    7: "surprised",
}

CLASS_NAMES: List[str] = [ID_TO_EMOTION[i] for i in range(NUM_CLASSES)]


class LabelMappingError(RuntimeError):
    """Raised when emotion / label IDs do not match the locked mapping."""


def _assert_mapping_integrity() -> None:
    if len(EMOTION_TO_ID) != NUM_CLASSES:
        raise LabelMappingError(
            f"EMOTION_TO_ID must have {NUM_CLASSES} entries, got {len(EMOTION_TO_ID)}"
        )
    if len(ID_TO_EMOTION) != NUM_CLASSES:
        raise LabelMappingError(
            f"ID_TO_EMOTION must have {NUM_CLASSES} entries, got {len(ID_TO_EMOTION)}"
        )
    if set(ID_TO_EMOTION.values()) != set(EMOTION_TO_ID.keys()):
        raise LabelMappingError("EMOTION_TO_ID and ID_TO_EMOTION keys/values disagree")
    for name, idx in EMOTION_TO_ID.items():
        if ID_TO_EMOTION.get(idx) != name:
            raise LabelMappingError(
                f"Bidirectional mismatch: EMOTION_TO_ID[{name!r}]={idx} "
                f"but ID_TO_EMOTION[{idx}]={ID_TO_EMOTION.get(idx)!r}"
            )
    if sorted(ID_TO_EMOTION.keys()) != list(range(NUM_CLASSES)):
        raise LabelMappingError(
            f"Label IDs must be exactly 0..{NUM_CLASSES - 1}, got {sorted(ID_TO_EMOTION)}"
        )


_assert_mapping_integrity()


def emotion_to_id(emotion: str) -> int:
    key = emotion.strip().lower()
    if key not in EMOTION_TO_ID:
        raise LabelMappingError(
            f"Unknown emotion {emotion!r}. Expected one of {CLASS_NAMES}"
        )
    return EMOTION_TO_ID[key]


def id_to_emotion(label_id: int) -> str:
    label_id = int(label_id)
    if label_id not in ID_TO_EMOTION:
        raise LabelMappingError(
            f"Unknown label id {label_id}. Expected 0..{NUM_CLASSES - 1}"
        )
    return ID_TO_EMOTION[label_id]


def num_classifier_logits() -> int:
    return NUM_CLASSES


@dataclass
class LabelVerificationReport:
    ok: bool
    num_classes: int
    emotion_to_id: Dict[str, int]
    issues: List[str] = field(default_factory=list)
    split_emotion_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_text(self) -> str:
        status = "PASSED" if self.ok else "FAILED"
        lines = [
            "RAVDESS Emotion Label Verification (Section 4)",
            "=" * 60,
            f"Status: {status}",
            f"NUM_CLASSES (classifier logits): {self.num_classes}",
            "",
            "Locked EMOTION_TO_ID:",
        ]
        for name, idx in sorted(self.emotion_to_id.items(), key=lambda x: x[1]):
            lines.append(f"  {idx}: {name}")
        lines.append("")
        lines.append("Emotion counts per split:")
        for split_name, counts in self.split_emotion_counts.items():
            lines.append(f"  {split_name}:")
            for emotion in CLASS_NAMES:
                lines.append(f"    {emotion}: {counts.get(emotion, 0)}")
            missing = [e for e in CLASS_NAMES if counts.get(e, 0) == 0]
            if missing:
                lines.append(f"    MISSING: {missing}")
        if self.issues:
            lines.append("")
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")
        else:
            lines.append("")
            lines.append("All metadata labels match the locked 8-class mapping.")
        return "\n".join(lines) + "\n"


def verify_labels_in_dataframe(
    df: pd.DataFrame,
    split_name: str,
    issues: List[str],
) -> Dict[str, int]:
    counts = {e: 0 for e in CLASS_NAMES}
    if "emotion" not in df.columns or "label" not in df.columns:
        issues.append(f"{split_name}: missing emotion/label columns")
        return counts

    for idx, row in df.iterrows():
        emotion = str(row["emotion"]).strip().lower()
        label = int(row["label"])
        filename = row.get("filename", f"row_{idx}")

        if emotion not in EMOTION_TO_ID:
            issues.append(f"{split_name}/{filename}: unknown emotion {emotion!r}")
            continue

        expected = EMOTION_TO_ID[emotion]
        if label != expected:
            issues.append(
                f"{split_name}/{filename}: label={label} but emotion={emotion!r} "
                f"expects {expected}"
            )
            continue

        if id_to_emotion(label) != emotion:
            issues.append(
                f"{split_name}/{filename}: reverse map failed for label={label}"
            )
            continue

        counts[emotion] += 1

    missing = [e for e, n in counts.items() if n == 0]
    if missing:
        issues.append(f"{split_name}: missing emotions {missing}")

    return counts


def verify_emotion_classes(bundle: "DatasetBundle") -> LabelVerificationReport:
    issues: List[str] = []
    split_counts: Dict[str, Dict[str, int]] = {}

    try:
        _assert_mapping_integrity()
    except LabelMappingError as exc:
        issues.append(str(exc))

    for split_name, df in (
        ("train", bundle.train),
        ("validation", bundle.validation),
        ("test", bundle.test),
    ):
        split_counts[split_name] = verify_labels_in_dataframe(df, split_name, issues)

    all_labels = set()
    for df in (bundle.train, bundle.validation, bundle.test):
        all_labels.update(int(x) for x in df["label"].unique())
    if all_labels != set(range(NUM_CLASSES)):
        issues.append(
            f"Dataset label set {sorted(all_labels)} != expected {list(range(NUM_CLASSES))}"
        )

    return LabelVerificationReport(
        ok=len(issues) == 0,
        num_classes=NUM_CLASSES,
        emotion_to_id=dict(EMOTION_TO_ID),
        issues=issues,
        split_emotion_counts=split_counts,
    )


def assert_emotion_classes(bundle: "DatasetBundle") -> LabelVerificationReport:
    """Hard gate: stop if label mapping is inconsistent."""
    report = verify_emotion_classes(bundle)
    if not report.ok:
        message = (
            "EMOTION LABEL VERIFICATION FAILED — stopping.\n"
            + "\n".join(f"  - {i}" for i in report.issues)
        )
        logger.error(message)
        raise LabelMappingError(message)
    logger.info(
        "Emotion classes OK | NUM_CLASSES=%d | logits=%d | classes=%s",
        NUM_CLASSES,
        num_classifier_logits(),
        CLASS_NAMES,
    )
    return report
