#!/usr/bin/env python3
"""
RAVDESS Dataset Preprocessing Pipeline
======================================
Speech-only audio preprocessing for Speech Emotion Recognition experiments.

Filters: modality=03 (audio-only), vocal_channel=01 (speech).
Output: mono 16 kHz WAV + actor-independent metadata splits.

Does NOT perform model training, feature extraction, or embedding generation.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import re
import shutil
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import soundfile as sf
from scipy import signal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEED = 42
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1

EMOTION_MAP: Dict[int, str] = {
    1: "neutral",
    2: "calm",
    3: "happy",
    4: "sad",
    5: "angry",
    6: "fearful",
    7: "disgust",
    8: "surprised",
}

LABEL_MAP: Dict[str, int] = {
    "neutral": 0,
    "calm": 1,
    "happy": 2,
    "sad": 3,
    "angry": 4,
    "fearful": 5,
    "disgust": 6,
    "surprised": 7,
}

INTENSITY_MAP: Dict[int, str] = {
    1: "normal",
    2: "strong",
}

STATEMENT_MAP: Dict[int, str] = {
    1: "statement_1",
    2: "statement_2",
}

REPETITION_MAP: Dict[int, str] = {
    1: "first",
    2: "second",
}

MODALITY_AUDIO_ONLY = 3
VOCAL_CHANNEL_SPEECH = 1

TRAIN_ACTORS = set(range(1, 17))       # 01–16
VALIDATION_ACTORS = set(range(17, 21))  # 17–20
TEST_ACTORS = set(range(21, 25))        # 21–24

FILENAME_PATTERN = re.compile(
    r"^(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})\.wav$",
    re.IGNORECASE,
)

METADATA_COLUMNS = [
    "filepath",
    "original_filepath",
    "filename",
    "modality",
    "vocal_channel",
    "emotion_id",
    "emotion",
    "intensity_id",
    "intensity",
    "statement_id",
    "statement",
    "repetition_id",
    "repetition",
    "actor_id",
    "label",
    "duration",
    "sample_rate",
    "num_channels",
    "split",
    "audio_hash",
]

logger = logging.getLogger("ravdess_preprocess")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ParsedFilename:
    filename: str
    modality: int
    vocal_channel: int
    emotion_id: int
    emotion: str
    intensity_id: int
    intensity: str
    statement_id: int
    statement: str
    repetition_id: int
    repetition: str
    actor_id: int
    label: int


@dataclass
class AudioInfo:
    duration: float
    sample_rate: int
    num_channels: int
    audio_hash: str
    valid: bool
    error: Optional[str] = None


@dataclass
class ProcessingResult:
    original_filepath: str
    filepath: str
    filename: str
    parsed: ParsedFilename
    audio: AudioInfo
    split: str
    success: bool
    error: Optional[str] = None


@dataclass
class PipelineCounters:
    discovered: int = 0
    speech_selected: int = 0
    song_excluded: int = 0
    video_only_excluded: int = 0
    other_excluded: int = 0
    successfully_processed: int = 0
    failed: int = 0
    parse_failed: int = 0


# ---------------------------------------------------------------------------
# RAVDESSParser
# ---------------------------------------------------------------------------

class RAVDESSParser:
    """Parse RAVDESS filenames and discover eligible speech audio files."""

    def __init__(
        self,
        input_dir: Path,
        modality: int = MODALITY_AUDIO_ONLY,
        vocal_channel: int = VOCAL_CHANNEL_SPEECH,
    ) -> None:
        self.input_dir = Path(input_dir)
        self.modality = modality
        self.vocal_channel = vocal_channel
        self.counters = PipelineCounters()

    @staticmethod
    def parse_filename(filename: str) -> Optional[ParsedFilename]:
        match = FILENAME_PATTERN.match(filename)
        if not match:
            return None

        modality = int(match.group(1))
        vocal_channel = int(match.group(2))
        emotion_id = int(match.group(3))
        intensity_id = int(match.group(4))
        statement_id = int(match.group(5))
        repetition_id = int(match.group(6))
        actor_id = int(match.group(7))

        if emotion_id not in EMOTION_MAP:
            return None
        if intensity_id not in INTENSITY_MAP:
            return None
        if statement_id not in STATEMENT_MAP:
            return None
        if repetition_id not in REPETITION_MAP:
            return None
        if actor_id < 1 or actor_id > 24:
            return None

        emotion = EMOTION_MAP[emotion_id]
        return ParsedFilename(
            filename=filename,
            modality=modality,
            vocal_channel=vocal_channel,
            emotion_id=emotion_id,
            emotion=emotion,
            intensity_id=intensity_id,
            intensity=INTENSITY_MAP[intensity_id],
            statement_id=statement_id,
            statement=STATEMENT_MAP[statement_id],
            repetition_id=repetition_id,
            repetition=REPETITION_MAP[repetition_id],
            actor_id=actor_id,
            label=LABEL_MAP[emotion],
        )

    def discover_wav_files(self) -> List[Path]:
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")

        files = sorted(self.input_dir.rglob("*.wav"))
        # Also catch .WAV
        files.extend(sorted(self.input_dir.rglob("*.WAV")))
        # Deduplicate while preserving order
        seen = set()
        unique: List[Path] = []
        for path in files:
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique.append(path)

        self.counters.discovered = len(unique)
        logger.info("Found %d WAV files", len(unique))
        return unique

    def select_speech_files(
        self, wav_files: Sequence[Path]
    ) -> List[Tuple[Path, ParsedFilename]]:
        selected: List[Tuple[Path, ParsedFilename]] = []

        for path in wav_files:
            parsed = self.parse_filename(path.name)
            if parsed is None:
                self.counters.parse_failed += 1
                self.counters.other_excluded += 1
                logger.warning("Could not parse filename: %s", path.name)
                continue

            if parsed.vocal_channel == 2:
                self.counters.song_excluded += 1
                continue

            if parsed.modality == 2:
                self.counters.video_only_excluded += 1
                continue

            if parsed.modality != self.modality or parsed.vocal_channel != self.vocal_channel:
                self.counters.other_excluded += 1
                continue

            selected.append((path, parsed))

        self.counters.speech_selected = len(selected)
        logger.info("Speech files selected: %d", self.counters.speech_selected)
        logger.info("Song files excluded: %d", self.counters.song_excluded)
        logger.info("Video-only files excluded: %d", self.counters.video_only_excluded)
        logger.info("Other excluded / parse failures: %d", self.counters.other_excluded)
        return selected


# ---------------------------------------------------------------------------
# AudioProcessor
# ---------------------------------------------------------------------------

class AudioProcessor:
    """Convert audio to mono 16 kHz WAV and validate quality."""

    def __init__(
        self,
        output_audio_dir: Path,
        target_sr: int = TARGET_SAMPLE_RATE,
    ) -> None:
        self.output_audio_dir = Path(output_audio_dir)
        self.target_sr = target_sr
        self.failed_records: List[Dict[str, str]] = []

    @staticmethod
    def _to_mono(audio: np.ndarray) -> np.ndarray:
        if audio.ndim == 1:
            return audio.astype(np.float64, copy=False)
        # soundfile returns (frames, channels)
        return np.mean(audio, axis=1).astype(np.float64, copy=False)

    @staticmethod
    def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        if orig_sr == target_sr:
            return audio
        # Deterministic polyphase resampling
        gcd = np.gcd(orig_sr, target_sr)
        up = target_sr // gcd
        down = orig_sr // gcd
        return signal.resample_poly(audio, up, down).astype(np.float64, copy=False)

    @staticmethod
    def compute_sha256(path: Path) -> str:
        hasher = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def validate_audio(self, path: Path) -> AudioInfo:
        try:
            if not path.exists():
                return AudioInfo(0.0, 0, 0, "", False, "File does not exist")

            audio, sr = sf.read(str(path), always_2d=False)
            audio = np.asarray(audio)

            if audio.size == 0:
                return AudioInfo(0.0, sr, 0, "", False, "Empty audio")

            num_channels = 1 if audio.ndim == 1 else audio.shape[-1]
            duration = float(audio.shape[0] / sr) if sr > 0 else 0.0

            if sr != self.target_sr:
                return AudioInfo(
                    duration, sr, num_channels, "", False,
                    f"Sample rate {sr} != {self.target_sr}",
                )
            if num_channels != TARGET_CHANNELS:
                return AudioInfo(
                    duration, sr, num_channels, "", False,
                    f"Channels {num_channels} != {TARGET_CHANNELS}",
                )
            if duration <= 0:
                return AudioInfo(duration, sr, num_channels, "", False, "Duration <= 0")
            if not np.isfinite(audio).all():
                return AudioInfo(
                    duration, sr, num_channels, "", False, "NaN or Inf values present"
                )

            audio_hash = self.compute_sha256(path)
            return AudioInfo(duration, sr, num_channels, audio_hash, True, None)
        except Exception as exc:  # noqa: BLE001
            return AudioInfo(0.0, 0, 0, "", False, str(exc))

    def process_file(
        self, source_path: Path, parsed: ParsedFilename
    ) -> Tuple[Optional[Path], AudioInfo]:
        actor_dir = self.output_audio_dir / f"Actor_{parsed.actor_id:02d}"
        actor_dir.mkdir(parents=True, exist_ok=True)
        dest_path = actor_dir / parsed.filename

        try:
            audio, orig_sr = sf.read(str(source_path), always_2d=False)
            audio = np.asarray(audio, dtype=np.float64)

            if audio.size == 0:
                info = AudioInfo(0.0, 0, 0, "", False, "Empty source audio")
                self._record_failure(source_path, parsed.filename, info.error or "")
                return None, info

            audio = self._to_mono(audio)
            audio = self._resample(audio, int(orig_sr), self.target_sr)

            if not np.isfinite(audio).all():
                info = AudioInfo(0.0, self.target_sr, 1, "", False, "NaN/Inf after processing")
                self._record_failure(source_path, parsed.filename, info.error or "")
                return None, info

            if audio.shape[0] == 0:
                info = AudioInfo(0.0, self.target_sr, 1, "", False, "Zero-length after resample")
                self._record_failure(source_path, parsed.filename, info.error or "")
                return None, info

            # Peak-normalize only if needed to stay in [-1, 1] without changing content shape
            peak = np.max(np.abs(audio))
            if peak > 1.0:
                audio = audio / peak

            sf.write(str(dest_path), audio.astype(np.float32), self.target_sr, subtype="PCM_16")

            info = self.validate_audio(dest_path)
            if not info.valid:
                self._record_failure(source_path, parsed.filename, info.error or "Validation failed")
                if dest_path.exists():
                    dest_path.unlink()
                return None, info

            return dest_path, info
        except Exception as exc:  # noqa: BLE001
            info = AudioInfo(0.0, 0, 0, "", False, str(exc))
            self._record_failure(source_path, parsed.filename, str(exc))
            if dest_path.exists():
                dest_path.unlink()
            return None, info

    def _record_failure(self, source_path: Path, filename: str, error: str) -> None:
        self.failed_records.append(
            {
                "original_filepath": str(source_path.resolve()),
                "filename": filename,
                "error": error,
            }
        )
        logger.error("Failed processing %s: %s", filename, error)

    def write_failed_log(self, log_path: Path) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(self.failed_records, columns=["original_filepath", "filename", "error"])
        df.to_csv(log_path, index=False)
        logger.info("Failed-file log written: %s (%d rows)", log_path, len(df))


# ---------------------------------------------------------------------------
# DatasetSplitter
# ---------------------------------------------------------------------------

class DatasetSplitter:
    """Actor-independent train / validation / test split."""

    def __init__(
        self,
        train_actors: set = TRAIN_ACTORS,
        validation_actors: set = VALIDATION_ACTORS,
        test_actors: set = TEST_ACTORS,
    ) -> None:
        self.train_actors = set(train_actors)
        self.validation_actors = set(validation_actors)
        self.test_actors = set(test_actors)
        self._validate_actor_partitions()

    def _validate_actor_partitions(self) -> None:
        all_actors = self.train_actors | self.validation_actors | self.test_actors
        overlap_tv = self.train_actors & self.validation_actors
        overlap_tt = self.train_actors & self.test_actors
        overlap_vt = self.validation_actors & self.test_actors
        if overlap_tv or overlap_tt or overlap_vt:
            raise ValueError(
                f"Actor split overlap detected: "
                f"train∩val={sorted(overlap_tv)}, "
                f"train∩test={sorted(overlap_tt)}, "
                f"val∩test={sorted(overlap_vt)}"
            )
        expected = set(range(1, 25))
        if all_actors != expected:
            missing = expected - all_actors
            extra = all_actors - expected
            raise ValueError(f"Actor coverage incomplete. Missing={sorted(missing)} Extra={sorted(extra)}")

    def assign_split(self, actor_id: int) -> str:
        if actor_id in self.train_actors:
            return "train"
        if actor_id in self.validation_actors:
            return "validation"
        if actor_id in self.test_actors:
            return "test"
        raise ValueError(f"Actor {actor_id} is not assigned to any split")

    def verify_no_actor_leakage(self, df: pd.DataFrame) -> List[str]:
        issues: List[str] = []
        actor_splits = df.groupby("actor_id")["split"].nunique()
        leaking = actor_splits[actor_splits > 1]
        for actor_id, n_splits in leaking.items():
            splits = sorted(df.loc[df["actor_id"] == actor_id, "split"].unique())
            issues.append(f"Actor {actor_id:02d} appears in {n_splits} splits: {splits}")
        return issues


# ---------------------------------------------------------------------------
# MetadataBuilder
# ---------------------------------------------------------------------------

class MetadataBuilder:
    """Build and persist dataset metadata CSVs."""

    def __init__(self, metadata_dir: Path) -> None:
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def build_dataframe(self, results: Sequence[ProcessingResult]) -> pd.DataFrame:
        rows = []
        for result in results:
            if not result.success:
                continue
            p = result.parsed
            a = result.audio
            rows.append(
                {
                    "filepath": result.filepath,
                    "original_filepath": result.original_filepath,
                    "filename": result.filename,
                    "modality": p.modality,
                    "vocal_channel": p.vocal_channel,
                    "emotion_id": p.emotion_id,
                    "emotion": p.emotion,
                    "intensity_id": p.intensity_id,
                    "intensity": p.intensity,
                    "statement_id": p.statement_id,
                    "statement": p.statement,
                    "repetition_id": p.repetition_id,
                    "repetition": p.repetition,
                    "actor_id": p.actor_id,
                    "label": p.label,
                    "duration": round(a.duration, 6),
                    "sample_rate": a.sample_rate,
                    "num_channels": a.num_channels,
                    "split": result.split,
                    "audio_hash": a.audio_hash,
                }
            )

        df = pd.DataFrame(rows, columns=METADATA_COLUMNS)
        if not df.empty:
            df = df.sort_values(["actor_id", "filename"], kind="mergesort").reset_index(drop=True)
        return df

    def write_csvs(self, df: pd.DataFrame) -> Dict[str, Path]:
        paths: Dict[str, Path] = {}

        full_path = self.metadata_dir / "ravdess_metadata.csv"
        df.to_csv(full_path, index=False)
        paths["full"] = full_path

        for split_name in ("train", "validation", "test"):
            split_df = df[df["split"] == split_name].reset_index(drop=True)
            split_path = self.metadata_dir / f"{split_name}.csv"
            split_df.to_csv(split_path, index=False)
            paths[split_name] = split_path
            logger.info("%s: %d files", split_name.capitalize(), len(split_df))

        logger.info("Metadata written to %s", self.metadata_dir)
        return paths


# ---------------------------------------------------------------------------
# DatasetValidator
# ---------------------------------------------------------------------------

class DatasetValidator:
    """Validate processed dataset integrity and detect leakage / inconsistency."""

    def __init__(self, splitter: DatasetSplitter) -> None:
        self.splitter = splitter
        self.issues: List[str] = []
        self.checklist: Dict[str, bool] = {}
        self.duplicate_audio_rows: List[Dict[str, object]] = []

    def validate(self, df: pd.DataFrame, audio_root: Path) -> Dict[str, bool]:
        self.issues = []
        checks: Dict[str, bool] = {}

        if df.empty:
            self.issues.append("Metadata dataframe is empty")
            return {k: False for k in self._checklist_keys()}

        # Modality / vocal channel
        checks["only_modality_03"] = bool((df["modality"] == 3).all())
        checks["only_vocal_channel_01"] = bool((df["vocal_channel"] == 1).all())
        if not checks["only_modality_03"]:
            self.issues.append("Non-audio-only modality found")
        if not checks["only_vocal_channel_01"]:
            self.issues.append("Non-speech vocal channel found")

        # Emotions
        emotions_present = set(df["emotion"].unique())
        expected_emotions = set(EMOTION_MAP.values())
        checks["all_8_emotions"] = emotions_present == expected_emotions
        if not checks["all_8_emotions"]:
            self.issues.append(
                f"Emotion mismatch. Missing={sorted(expected_emotions - emotions_present)} "
                f"Extra={sorted(emotions_present - expected_emotions)}"
            )

        # Audio format checks from metadata
        checks["all_wav"] = bool(df["filename"].str.lower().str.endswith(".wav").all())
        checks["all_mono"] = bool((df["num_channels"] == 1).all())
        checks["all_16khz"] = bool((df["sample_rate"] == TARGET_SAMPLE_RATE).all())
        checks["no_zero_duration"] = bool((df["duration"] > 0).all())

        # Spot-check a sample of files for NaN/Inf by reloading
        corrupted = 0
        nan_inf = 0
        for _, row in df.sample(n=min(50, len(df)), random_state=SEED).iterrows():
            path = Path(row["filepath"])
            if not path.is_absolute():
                path = audio_root.parent / path
            if not path.exists():
                # try relative to audio root parent (output_dir)
                alt = Path(row["filepath"])
                if not alt.exists():
                    corrupted += 1
                    continue
                path = alt
            try:
                audio, sr = sf.read(str(path))
                if sr != TARGET_SAMPLE_RATE:
                    corrupted += 1
                if not np.isfinite(audio).all():
                    nan_inf += 1
            except Exception:  # noqa: BLE001
                corrupted += 1

        checks["no_corrupted_audio"] = corrupted == 0
        checks["no_nan_inf"] = nan_inf == 0
        if corrupted:
            self.issues.append(f"Corrupted / unloadable audio in sample check: {corrupted}")
        if nan_inf:
            self.issues.append(f"NaN/Inf audio in sample check: {nan_inf}")

        # Actor preservation
        checks["actor_info_preserved"] = (
            "actor_id" in df.columns and df["actor_id"].notna().all() and df["actor_id"].between(1, 24).all()
        )

        # Actor-independent split
        leakage = self.splitter.verify_no_actor_leakage(df)
        checks["actor_independent_split"] = len(leakage) == 0 and set(df["split"].unique()) <= {
            "train", "validation", "test"
        }
        checks["no_actor_leakage"] = len(leakage) == 0
        self.issues.extend(leakage)

        # Duplicates
        dup_names = df["filename"].duplicated().sum()
        dup_paths = df["filepath"].duplicated().sum()
        checks["no_duplicate_paths"] = dup_paths == 0 and dup_names == 0
        if dup_names:
            self.issues.append(f"Duplicate filenames: {int(dup_names)}")
        if dup_paths:
            self.issues.append(f"Duplicate filepaths: {int(dup_paths)}")

        # Duplicate audio hashes
        self.duplicate_audio_rows: List[Dict[str, object]] = []
        if "audio_hash" in df.columns:
            dup_mask = df.duplicated("audio_hash", keep=False)
            dup_hash_count = int(df["audio_hash"].duplicated().sum())
            if dup_hash_count:
                dup_df = df.loc[dup_mask, ["filename", "filepath", "actor_id", "emotion", "audio_hash", "split"]]
                self.duplicate_audio_rows = dup_df.to_dict(orient="records")
                self.issues.append(
                    f"Duplicate audio hashes (exact duplicates): {dup_hash_count}"
                )
                for hash_val, group in dup_df.groupby("audio_hash"):
                    names = ", ".join(group["filename"].tolist())
                    self.issues.append(f"  hash={hash_val[:12]}... files=[{names}]")
            checks["no_duplicate_audio_hashes"] = dup_hash_count == 0
        else:
            checks["no_duplicate_audio_hashes"] = True

        # Metadata consistency with filename encoding
        inconsistent = self._check_filename_consistency(df)
        checks["metadata_matches_filenames"] = len(inconsistent) == 0
        self.issues.extend(inconsistent[:20])  # cap reported issues

        # Split CSVs presence will be checked by caller; mark based on data
        checks["train_csv_ready"] = (df["split"] == "train").any()
        checks["validation_csv_ready"] = (df["split"] == "validation").any()
        checks["test_csv_ready"] = (df["split"] == "test").any()

        # Emotions in each split
        for split_name in ("train", "validation", "test"):
            split_emotions = set(df.loc[df["split"] == split_name, "emotion"].unique())
            key = f"all_emotions_in_{split_name}"
            checks[key] = split_emotions == expected_emotions
            if not checks[key]:
                missing = sorted(expected_emotions - split_emotions)
                self.issues.append(f"Missing emotions in {split_name}: {missing}")

        checks["no_model_training_code"] = True  # this module is preprocessing-only

        self.checklist = checks
        return checks

    @staticmethod
    def _check_filename_consistency(df: pd.DataFrame) -> List[str]:
        issues: List[str] = []
        for _, row in df.iterrows():
            parsed = RAVDESSParser.parse_filename(row["filename"])
            if parsed is None:
                issues.append(f"Unparseable filename in metadata: {row['filename']}")
                continue
            checks = [
                ("modality", parsed.modality, row["modality"]),
                ("vocal_channel", parsed.vocal_channel, row["vocal_channel"]),
                ("emotion_id", parsed.emotion_id, row["emotion_id"]),
                ("emotion", parsed.emotion, row["emotion"]),
                ("intensity_id", parsed.intensity_id, row["intensity_id"]),
                ("intensity", parsed.intensity, row["intensity"]),
                ("statement_id", parsed.statement_id, row["statement_id"]),
                ("statement", parsed.statement, row["statement"]),
                ("repetition_id", parsed.repetition_id, row["repetition_id"]),
                ("repetition", parsed.repetition, row["repetition"]),
                ("actor_id", parsed.actor_id, row["actor_id"]),
                ("label", parsed.label, row["label"]),
            ]
            for field_name, expected, actual in checks:
                if expected != actual:
                    issues.append(
                        f"{row['filename']}: {field_name} mismatch "
                        f"(filename={expected}, metadata={actual})"
                    )
        return issues

    @staticmethod
    def _checklist_keys() -> List[str]:
        return [
            "only_modality_03",
            "only_vocal_channel_01",
            "all_8_emotions",
            "all_wav",
            "all_mono",
            "all_16khz",
            "no_zero_duration",
            "no_corrupted_audio",
            "no_nan_inf",
            "actor_info_preserved",
            "actor_independent_split",
            "no_actor_leakage",
            "no_duplicate_paths",
            "no_duplicate_audio_hashes",
            "metadata_matches_filenames",
            "train_csv_ready",
            "validation_csv_ready",
            "test_csv_ready",
            "all_emotions_in_train",
            "all_emotions_in_validation",
            "all_emotions_in_test",
            "no_model_training_code",
        ]

    def format_checklist(self) -> str:
        lines = ["Final Validation Checklist", "=" * 40]
        for key in self._checklist_keys():
            passed = self.checklist.get(key, False)
            mark = "x" if passed else " "
            lines.append(f"[{mark}] {key}")
        if self.issues:
            lines.append("")
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")
        else:
            lines.append("")
            lines.append("No issues found.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# StatisticsGenerator
# ---------------------------------------------------------------------------

class StatisticsGenerator:
    """Generate dataset statistics and class-balance reports."""

    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, df: pd.DataFrame, counters: PipelineCounters, elapsed: float) -> Dict[str, Path]:
        paths: Dict[str, Path] = {}

        # Emotion distribution
        emotion_rows = []
        total = len(df)
        total_duration = float(df["duration"].sum()) if total else 0.0
        for emotion in EMOTION_MAP.values():
            subset = df[df["emotion"] == emotion]
            n = len(subset)
            emotion_rows.append(
                {
                    "emotion": emotion,
                    "number_of_samples": n,
                    "percentage": round(100.0 * n / total, 4) if total else 0.0,
                    "total_duration": round(float(subset["duration"].sum()), 4),
                }
            )
        emotion_df = pd.DataFrame(emotion_rows)
        emotion_path = self.reports_dir / "emotion_distribution.csv"
        emotion_df.to_csv(emotion_path, index=False)
        paths["emotion"] = emotion_path

        # Actor distribution
        actor_rows = []
        for actor_id, group in df.groupby("actor_id"):
            splits = sorted(group["split"].unique())
            actor_rows.append(
                {
                    "actor_id": int(actor_id),
                    "number_of_files": len(group),
                    "total_duration": round(float(group["duration"].sum()), 4),
                    "split": splits[0] if len(splits) == 1 else ",".join(splits),
                }
            )
        actor_df = pd.DataFrame(actor_rows).sort_values("actor_id")
        actor_path = self.reports_dir / "actor_distribution.csv"
        actor_df.to_csv(actor_path, index=False)
        paths["actor"] = actor_path

        # Split distribution / dataset statistics summary table
        stats_rows = []
        stats_rows.append(
            {
                "category": "total",
                "name": "all",
                "number_of_samples": total,
                "number_of_actors": int(df["actor_id"].nunique()) if total else 0,
                "total_duration": round(total_duration, 4),
                "number_of_emotions": int(df["emotion"].nunique()) if total else 0,
            }
        )
        for split_name in ("train", "validation", "test"):
            subset = df[df["split"] == split_name]
            stats_rows.append(
                {
                    "category": "split",
                    "name": split_name,
                    "number_of_samples": len(subset),
                    "number_of_actors": int(subset["actor_id"].nunique()),
                    "total_duration": round(float(subset["duration"].sum()), 4),
                    "number_of_emotions": int(subset["emotion"].nunique()),
                }
            )
        for _, erow in emotion_df.iterrows():
            stats_rows.append(
                {
                    "category": "emotion",
                    "name": erow["emotion"],
                    "number_of_samples": int(erow["number_of_samples"]),
                    "number_of_actors": int(
                        df.loc[df["emotion"] == erow["emotion"], "actor_id"].nunique()
                    ),
                    "total_duration": float(erow["total_duration"]),
                    "number_of_emotions": 1,
                }
            )
        stats_df = pd.DataFrame(stats_rows)
        stats_path = self.reports_dir / "dataset_statistics.csv"
        stats_df.to_csv(stats_path, index=False)
        paths["statistics"] = stats_path

        # Class balance check (per split)
        balance_lines = ["Class Balance Check", "=" * 40]
        expected = set(EMOTION_MAP.values())
        for split_name in ("train", "validation", "test"):
            subset = df[df["split"] == split_name]
            present = set(subset["emotion"].unique())
            missing = sorted(expected - present)
            balance_lines.append(f"\n{split_name}:")
            balance_lines.append(f"  samples={len(subset)}")
            for emotion in EMOTION_MAP.values():
                n = int((subset["emotion"] == emotion).sum())
                pct = 100.0 * n / len(subset) if len(subset) else 0.0
                balance_lines.append(f"  {emotion}: {n} ({pct:.2f}%)")
            if missing:
                balance_lines.append(f"  MISSING emotions: {missing}")
            else:
                balance_lines.append("  All 8 emotions represented.")
        balance_lines.append(
            "\nNote: No oversampling, undersampling, SMOTE, or augmentation applied."
        )
        balance_path = self.reports_dir / "class_balance_report.txt"
        balance_path.write_text("\n".join(balance_lines) + "\n", encoding="utf-8")
        paths["class_balance"] = balance_path

        # Preprocessing summary
        summary_lines = [
            "RAVDESS Preprocessing Summary",
            "=" * 40,
            f"SEED: {SEED}",
            f"Target sample rate: {TARGET_SAMPLE_RATE}",
            f"Target channels: {TARGET_CHANNELS}",
            "",
            f"WAV files discovered: {counters.discovered}",
            f"Speech files selected: {counters.speech_selected}",
            f"Song files excluded: {counters.song_excluded}",
            f"Video-only files excluded: {counters.video_only_excluded}",
            f"Other excluded / parse failures: {counters.other_excluded}",
            f"Successfully processed: {counters.successfully_processed}",
            f"Failed: {counters.failed}",
            "",
            f"Total files in metadata: {total}",
            f"Total duration (seconds): {total_duration:.4f}",
            f"Unique actors: {df['actor_id'].nunique() if total else 0}",
            f"Emotions: {df['emotion'].nunique() if total else 0}",
            "",
            "Split distribution:",
        ]
        for split_name in ("train", "validation", "test"):
            subset = df[df["split"] == split_name]
            summary_lines.append(
                f"  {split_name}: samples={len(subset)}, "
                f"actors={subset['actor_id'].nunique()}, "
                f"duration={subset['duration'].sum():.4f}s"
            )
        summary_lines.append("")
        summary_lines.append("Emotion distribution:")
        for _, erow in emotion_df.iterrows():
            summary_lines.append(
                f"  {erow['emotion']}: {int(erow['number_of_samples'])} "
                f"({erow['percentage']:.2f}%), duration={erow['total_duration']:.4f}s"
            )
        summary_lines.append("")
        summary_lines.append(f"Total processing time (seconds): {elapsed:.2f}")
        summary_lines.append("")
        summary_lines.append("Actor split:")
        summary_lines.append(f"  train: {sorted(TRAIN_ACTORS)}")
        summary_lines.append(f"  validation: {sorted(VALIDATION_ACTORS)}")
        summary_lines.append(f"  test: {sorted(TEST_ACTORS)}")

        summary_path = self.reports_dir / "preprocessing_summary.txt"
        summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
        paths["summary"] = summary_path

        logger.info("Reports written to %s", self.reports_dir)
        return paths


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------

class RAVDESSPreprocessingPipeline:
    """End-to-end RAVDESS speech preprocessing pipeline."""

    def __init__(self, input_dir: Path, output_dir: Path) -> None:
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.audio_dir = self.output_dir / "audio"
        self.metadata_dir = self.output_dir / "metadata"
        self.reports_dir = self.output_dir / "reports"
        self.logs_dir = self.output_dir / "logs"
        self.preprocessing_dir = self.output_dir / "preprocessing"

        self.parser = RAVDESSParser(self.input_dir)
        self.processor = AudioProcessor(self.audio_dir)
        self.splitter = DatasetSplitter()
        self.metadata_builder = MetadataBuilder(self.metadata_dir)
        self.validator = DatasetValidator(self.splitter)
        self.stats = StatisticsGenerator(self.reports_dir)

    def _prepare_directories(self) -> None:
        for path in (
            self.audio_dir,
            self.metadata_dir,
            self.reports_dir,
            self.logs_dir,
            self.preprocessing_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

        # Keep a copy of this script under output for reproducibility
        script_src = Path(__file__).resolve()
        script_dst = self.preprocessing_dir / "preprocess_ravdess.py"
        if script_src != script_dst:
            shutil.copy2(script_src, script_dst)

    def run(self) -> pd.DataFrame:
        start = time.time()
        np.random.seed(SEED)
        self._prepare_directories()

        wav_files = self.parser.discover_wav_files()
        selected = self.parser.select_speech_files(wav_files)

        results: List[ProcessingResult] = []
        emotion_counts: Dict[str, int] = {e: 0 for e in EMOTION_MAP.values()}
        actor_counts: Dict[int, int] = {i: 0 for i in range(1, 25)}
        split_counts: Dict[str, int] = {"train": 0, "validation": 0, "test": 0}

        for idx, (source_path, parsed) in enumerate(selected, start=1):
            split = self.splitter.assign_split(parsed.actor_id)
            dest_path, audio_info = self.processor.process_file(source_path, parsed)

            if dest_path is None or not audio_info.valid:
                self.parser.counters.failed += 1
                results.append(
                    ProcessingResult(
                        original_filepath=str(source_path.resolve()),
                        filepath="",
                        filename=parsed.filename,
                        parsed=parsed,
                        audio=audio_info,
                        split=split,
                        success=False,
                        error=audio_info.error,
                    )
                )
                continue

            # Store filepath relative to output_dir for portability
            rel_filepath = str(dest_path.relative_to(self.output_dir))
            self.parser.counters.successfully_processed += 1
            emotion_counts[parsed.emotion] += 1
            actor_counts[parsed.actor_id] += 1
            split_counts[split] += 1

            results.append(
                ProcessingResult(
                    original_filepath=str(source_path.resolve()),
                    filepath=rel_filepath,
                    filename=parsed.filename,
                    parsed=parsed,
                    audio=audio_info,
                    split=split,
                    success=True,
                )
            )

            if idx % 100 == 0 or idx == len(selected):
                logger.info(
                    "Processed %d / %d files (ok=%d, failed=%d)",
                    idx,
                    len(selected),
                    self.parser.counters.successfully_processed,
                    self.parser.counters.failed,
                )

        self.processor.write_failed_log(self.logs_dir / "failed_audio_files.csv")

        df = self.metadata_builder.build_dataframe(results)
        self.metadata_builder.write_csvs(df)

        elapsed = time.time() - start
        self.stats.generate(df, self.parser.counters, elapsed)

        checks = self.validator.validate(df, self.audio_dir)
        checklist_text = self.validator.format_checklist()
        checklist_path = self.reports_dir / "validation_checklist.txt"
        checklist_path.write_text(checklist_text + "\n", encoding="utf-8")
        logger.info("\n%s", checklist_text)

        dup_log = self.logs_dir / "duplicate_audio_files.csv"
        dup_df = pd.DataFrame(
            self.validator.duplicate_audio_rows,
            columns=["filename", "filepath", "actor_id", "emotion", "audio_hash", "split"],
        )
        dup_df.to_csv(dup_log, index=False)
        if len(dup_df):
            logger.warning("Duplicate exact audio files logged to %s (%d rows)", dup_log, len(dup_df))
        else:
            logger.info("No duplicate audio hashes found.")

        # Summary logs
        logger.info("Successfully processed: %d", self.parser.counters.successfully_processed)
        logger.info("Failed: %d", self.parser.counters.failed)
        logger.info("Files per emotion: %s", emotion_counts)
        logger.info(
            "Files per actor: %s",
            {k: v for k, v in actor_counts.items() if v > 0},
        )
        logger.info("Train: %d", split_counts["train"])
        logger.info("Validation: %d", split_counts["validation"])
        logger.info("Test: %d", split_counts["test"])
        logger.info("Total processing time: %.2f seconds", elapsed)

        failed_checks = [k for k, v in checks.items() if not v]
        if failed_checks:
            logger.warning("Failed validation checks: %s", failed_checks)
        else:
            logger.info("All validation checks passed.")

        return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def setup_logging(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / "logs" / "preprocessing.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        ],
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RAVDESS speech-only dataset preprocessing pipeline"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Path to raw RAVDESS directory (contains Actor_* folders or nested WAVs)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Path to output directory (ravdess_preprocessed)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    setup_logging(output_dir)
    logger.info("RAVDESS preprocessing started")
    logger.info("Input: %s", input_dir)
    logger.info("Output: %s", output_dir)
    logger.info("SEED=%d", SEED)

    pipeline = RAVDESSPreprocessingPipeline(input_dir=input_dir, output_dir=output_dir)
    df = pipeline.run()

    logger.info("Done. Metadata rows: %d", len(df))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
