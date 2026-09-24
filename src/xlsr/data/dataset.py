"""
Load the existing preprocessed RAVDESS dataset.

Uses metadata/train.csv, validation.csv, test.csv as-is.
Does NOT create a new random or file-level split.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from xlsr.core.constants import SAMPLE_RATE
from xlsr.core.paths import (
    AUDIO_SUBDIR,
    DEFAULT_DATA_DIR,
    FULL_METADATA_CSV_NAME,
    METADATA_SUBDIR,
    PROJECT_ROOT,
    TEST_CSV_NAME,
    TRAIN_CSV_NAME,
    VALIDATION_CSV_NAME,
)
from xlsr.data.audio import load_raw_waveform
from xlsr.data.labels import EMOTION_TO_ID

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = (
    "filepath",
    "filename",
    "emotion",
    "label",
    "actor_id",
    "sample_rate",
    "num_channels",
    "split",
)

EXPECTED_TRAIN_ACTORS = set(range(1, 17))
EXPECTED_VAL_ACTORS = set(range(17, 21))
EXPECTED_TEST_ACTORS = set(range(21, 25))


@dataclass(frozen=True)
class DatasetBundle:
    """Container for the three existing split dataframes + resolved roots."""

    data_dir: Path
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame

    @property
    def sizes(self) -> Dict[str, int]:
        return {
            "train": len(self.train),
            "validation": len(self.validation),
            "test": len(self.test),
            "total": len(self.train) + len(self.validation) + len(self.test),
        }


class DatasetNotFoundError(FileNotFoundError):
    """Raised when the preprocessed dataset layout is missing."""


class DatasetIntegrityError(RuntimeError):
    """Raised when CSV contents violate expected preprocessing contracts."""


def _metadata_dir(data_dir: Path) -> Path:
    return data_dir / METADATA_SUBDIR


def _audio_dir(data_dir: Path) -> Path:
    return data_dir / AUDIO_SUBDIR


def validate_data_dir_structure(data_dir: Path) -> None:
    """Check that ravdess_preprocessed has the expected folders/files."""
    data_dir = Path(data_dir).resolve()
    if not data_dir.exists():
        raise DatasetNotFoundError(f"Data directory not found: {data_dir}")

    meta = _metadata_dir(data_dir)
    audio = _audio_dir(data_dir)
    required = [
        meta,
        audio,
        meta / TRAIN_CSV_NAME,
        meta / VALIDATION_CSV_NAME,
        meta / TEST_CSV_NAME,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise DatasetNotFoundError(
            "Preprocessed dataset structure incomplete. Missing:\n  - "
            + "\n  - ".join(missing)
        )

    if "ravdess" in data_dir.name.lower():
        actor_dirs = sorted(audio.glob("Actor_*"))
        if len(actor_dirs) < 24:
            logger.warning(
                "Expected 24 Actor_* folders under audio/; found %d", len(actor_dirs)
            )


def resolve_audio_path(data_dir: Path, filepath: str) -> Path:
    """Resolve a metadata filepath to an absolute path under data_dir."""
    data_dir = Path(data_dir).resolve()
    path = Path(filepath)
    if path.is_absolute():
        return path
    return (data_dir / path).resolve()


def _load_split_csv(path: Path, expected_split: str, data_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DatasetIntegrityError(
            f"{path.name} missing required columns: {missing_cols}"
        )

    if df.empty:
        raise DatasetIntegrityError(f"{path.name} is empty")

    bad_split = df.loc[df["split"] != expected_split]
    if len(bad_split):
        raise DatasetIntegrityError(
            f"{path.name}: found {len(bad_split)} rows with split != '{expected_split}'"
        )

    labels_path = data_dir / "metadata" / "labels.json"
    if labels_path.exists():
        import json
        mapping = json.loads(labels_path.read_text(encoding="utf-8"))
    else:
        mapping = EMOTION_TO_ID

    for _, row in df.iterrows():
        emotion = str(row["emotion"])
        label = int(row["label"])
        if emotion not in mapping:
            raise DatasetIntegrityError(f"Unknown emotion in {path.name}: {emotion}")
        if mapping[emotion] != label:
            raise DatasetIntegrityError(
                f"Label mismatch in {path.name} for {row['filename']}: "
                f"emotion={emotion} label={label} expected={mapping[emotion]}"
            )

    if not (df["sample_rate"] == SAMPLE_RATE).all():
        raise DatasetIntegrityError(
            f"{path.name}: sample_rate must be {SAMPLE_RATE} for all rows"
        )
    if not (df["num_channels"] == 1).all():
        raise DatasetIntegrityError(f"{path.name}: num_channels must be 1 for all rows")

    abs_paths = [str(resolve_audio_path(data_dir, fp)) for fp in df["filepath"]]
    df = df.copy()
    df["abs_filepath"] = abs_paths

    missing_files = [p for p in abs_paths if not Path(p).exists()]
    if missing_files:
        preview = "\n  - ".join(missing_files[:5])
        raise DatasetIntegrityError(
            f"{path.name}: {len(missing_files)} audio files missing. Examples:\n  - {preview}"
        )

    return df.reset_index(drop=True)


def load_ravdess_splits(data_dir: Path | str | None = None) -> DatasetBundle:
    """Load train / validation / test CSVs from the existing preprocessed dataset."""
    if data_dir is not None:
        p = Path(data_dir)
        if not p.is_absolute():
            if (PROJECT_ROOT / p).exists():
                root = (PROJECT_ROOT / p).resolve()
            elif (PROJECT_ROOT / "data" / p).exists():
                root = (PROJECT_ROOT / "data" / p).resolve()
            elif str(p).endswith("_preprocessed") and (PROJECT_ROOT / "data" / str(p).replace("_preprocessed", "")).exists():
                root = (PROJECT_ROOT / "data" / str(p).replace("_preprocessed", "")).resolve()
            else:
                root = p.resolve()
        else:
            root = p.resolve()
    else:
        root = DEFAULT_DATA_DIR.resolve()
    validate_data_dir_structure(root)

    meta = _metadata_dir(root)
    train = _load_split_csv(meta / TRAIN_CSV_NAME, "train", root)
    validation = _load_split_csv(meta / VALIDATION_CSV_NAME, "validation", root)
    test = _load_split_csv(meta / TEST_CSV_NAME, "test", root)

    bundle = DatasetBundle(
        data_dir=root,
        train=train,
        validation=validation,
        test=test,
    )
    logger.info(
        "Loaded existing splits from %s | train=%d validation=%d test=%d",
        root,
        len(train),
        len(validation),
        len(test),
    )
    return bundle


def get_actor_sets(bundle: DatasetBundle) -> Dict[str, set]:
    return {
        "train": set(int(a) for a in bundle.train["actor_id"].unique()),
        "validation": set(int(a) for a in bundle.validation["actor_id"].unique()),
        "test": set(int(a) for a in bundle.test["actor_id"].unique()),
    }


def verify_actor_independent_split(
    bundle: DatasetBundle, strict: bool = True
) -> Tuple[bool, list]:
    """Verify actor-independent split. Raises DatasetIntegrityError if strict and failed."""
    actors = get_actor_sets(bundle)
    issues = []

    if actors["train"] & actors["validation"]:
        issues.append(
            f"Train ∩ Validation actors = {sorted(actors['train'] & actors['validation'])}"
        )
    if actors["train"] & actors["test"]:
        issues.append(
            f"Train ∩ Test actors = {sorted(actors['train'] & actors['test'])}"
        )
    if actors["validation"] & actors["test"]:
        issues.append(
            f"Validation ∩ Test actors = {sorted(actors['validation'] & actors['test'])}"
        )

    if actors["train"] != EXPECTED_TRAIN_ACTORS:
        issues.append(
            f"Train actors mismatch. got={sorted(actors['train'])} "
            f"expected={sorted(EXPECTED_TRAIN_ACTORS)}"
        )
    if actors["validation"] != EXPECTED_VAL_ACTORS:
        issues.append(
            f"Validation actors mismatch. got={sorted(actors['validation'])} "
            f"expected={sorted(EXPECTED_VAL_ACTORS)}"
        )
    if actors["test"] != EXPECTED_TEST_ACTORS:
        issues.append(
            f"Test actors mismatch. got={sorted(actors['test'])} "
            f"expected={sorted(EXPECTED_TEST_ACTORS)}"
        )

    ok = len(issues) == 0
    if strict and not ok:
        raise DatasetIntegrityError(
            "Actor-independent split check failed:\n  - " + "\n  - ".join(issues)
        )
    return ok, issues


def write_dataset_summary(bundle: DatasetBundle, output_path: Path) -> Path:
    """Write a short dataset summary into the experiment output folder."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    actors = get_actor_sets(bundle)

    lines = [
        "RAVDESS Existing Dataset Summary (Section 2)",
        "=" * 50,
        f"data_dir: {bundle.data_dir}",
        f"train: {len(bundle.train)}",
        f"validation: {len(bundle.validation)}",
        f"test: {len(bundle.test)}",
        f"total: {bundle.sizes['total']}",
        "",
        "Actors (preserved from preprocessing; not re-split):",
        f"  train: {sorted(actors['train'])}",
        f"  validation: {sorted(actors['validation'])}",
        f"  test: {sorted(actors['test'])}",
        "",
        "Emotion counts (train):",
    ]
    for emotion, count in bundle.train["emotion"].value_counts().sort_index().items():
        lines.append(f"  {emotion}: {int(count)}")

    text = "\n".join(lines) + "\n"
    output_path.write_text(text, encoding="utf-8")
    logger.info("Dataset summary written: %s", output_path)
    return output_path


def load_full_metadata(data_dir: Path | str | None = None) -> Optional[pd.DataFrame]:
    """Optionally load ravdess_metadata.csv if present."""
    root = Path(data_dir).resolve() if data_dir is not None else DEFAULT_DATA_DIR.resolve()
    path = _metadata_dir(root) / FULL_METADATA_CSV_NAME
    if not path.exists():
        return None
    return pd.read_csv(path)


class RAVDESSXLSRDataset(Dataset):
    """
    PyTorch Dataset for preprocessed RAVDESS metadata.

    Loads raw 16 kHz mono WAV audio waveforms and mapped 8-class emotion labels.
    Preserves original filenames and actor IDs for evaluation/debugging.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        data_dir: Optional[Union[Path, str]] = None,
        max_samples: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.df = df.reset_index(drop=True)
        if max_samples is not None and max_samples > 0:
            self.df = self.df.iloc[:max_samples].reset_index(drop=True)

        self.data_dir = Path(data_dir).resolve() if data_dir else None

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        row = self.df.iloc[idx]
        filepath = str(row["abs_filepath"]) if "abs_filepath" in row else str(row["filepath"])
        
        # Load raw audio waveform (16000 Hz, mono)
        audio = load_raw_waveform(filepath, expected_sr=SAMPLE_RATE)
        
        return {
            "waveform": audio.waveform,  # 1D float32 numpy array
            "label": int(row["label"]),
            "filename": str(row["filename"]),
            "actor_id": int(row["actor_id"]),
            "emotion": str(row["emotion"]),
            "filepath": filepath,
        }


class SERDataCollator:
    """
    Custom collator for dynamic padding of variable-length audio waveforms.

    Pads waveforms dynamically within each batch to produce:
      - input_values (B, max_length)
      - attention_mask (B, max_length)
      - labels (B,)
    """

    def __init__(self, processor: Any) -> None:
        self.processor = processor

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        from xlsr.model.processor import waveforms_to_model_inputs

        waveforms = [item["waveform"] for item in features]
        labels = [item["label"] for item in features]

        # Convert waveforms into padded model inputs
        batch_inputs = waveforms_to_model_inputs(
            self.processor,
            waveforms=waveforms,
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )

        batch_inputs["labels"] = torch.tensor(labels, dtype=torch.long)
        return batch_inputs

