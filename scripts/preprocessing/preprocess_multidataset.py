#!/usr/bin/env python3
"""
Multi-Dataset Preprocessing Pipeline: RAVDESS + SAVEE
=====================================================
Preprocessing script to combine RAVDESS and SAVEE datasets:
1. Resamples all audio to 16 kHz, single-channel (mono) PCM 16-bit WAV.
2. Standardizes emotion categories into standard 8-class scheme (neutral, calm, happy, sad, angry, fearful, disgust, surprised).
3. Creates a combined preprocessed dataset directory `combined_preprocessed`.
4. Splits the combined dataset into 70% Train, 15% Validation, and 15% Test splits.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import soundfile as sf
from scipy import signal

def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for p in [current] + list(current.parents):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
    return Path(__file__).resolve().parents[2]

PROJECT_ROOT = _find_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
from xlsr.data.labels import EMOTION_TO_ID

TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1

LABEL_MAP: Dict[str, int] = EMOTION_TO_ID

RAVDESS_EMOTION_MAP: Dict[int, str] = {
    1: "neutral",
    2: "calm",
    3: "happy",
    4: "sad",
    5: "angry",
    6: "fearful",
    7: "disgust",
    8: "surprised",
}

SAVEE_EMOTION_MAP: Dict[str, str] = {
    "n": "neutral",
    "h": "happy",
    "sa": "sad",
    "a": "angry",
    "f": "fearful",
    "d": "disgust",
    "su": "surprised",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("preprocess_multidataset")


def compute_audio_hash(filepath: Path) -> str:
    """Compute SHA256 hash of file content."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def process_audio(
    input_path: Path, output_path: Path
) -> Tuple[float, int, int, str]:
    """
    Read, convert to mono 16kHz PCM WAV, and save to output_path.
    Returns: (duration_sec, sample_rate, num_channels, audio_hash)
    """
    audio_data, sr = sf.read(str(input_path), dtype="float32")

    # Convert stereo/multi-channel to mono
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Resample to 16 kHz if necessary
    if sr != TARGET_SAMPLE_RATE:
        import math
        gcd_val = math.gcd(TARGET_SAMPLE_RATE, int(sr))
        up = TARGET_SAMPLE_RATE // gcd_val
        down = int(sr) // gcd_val
        audio_data = signal.resample_poly(audio_data, up, down)
        sr = TARGET_SAMPLE_RATE

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio_data, TARGET_SAMPLE_RATE, subtype="PCM_16")

    duration = float(len(audio_data) / TARGET_SAMPLE_RATE)
    audio_hash = compute_audio_hash(output_path)

    return duration, TARGET_SAMPLE_RATE, TARGET_CHANNELS, audio_hash


def parse_ravdess(ravdess_dir: Path) -> List[Dict]:
    """Parse raw RAVDESS audio files."""
    records = []
    pattern = re.compile(
        r"^(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})\.wav$", re.IGNORECASE
    )

    wav_files = sorted(list(ravdess_dir.rglob("*.wav")))
    logger.info("Found %d WAV files in RAVDESS folder: %s", len(wav_files), ravdess_dir)

    for file in wav_files:
        match = pattern.match(file.name)
        if not match:
            continue
        parts = [int(p) for p in match.groups()]
        modality, vocal_channel, emotion_id, intensity, statement, repetition, actor_id = parts

        # Audio-only (modality 03)
        if modality != 3:
            continue

        emotion_str = RAVDESS_EMOTION_MAP.get(emotion_id)
        if not emotion_str or emotion_str not in LABEL_MAP:
            continue

        records.append({
            "dataset_name": "ravdess",
            "original_filepath": str(file.resolve()),
            "original_filename": file.name,
            "dest_subpath": f"audio/ravdess/Actor_{actor_id:02d}/ravdess_{file.name}",
            "emotion": emotion_str,
            "label": LABEL_MAP[emotion_str],
            "actor_id": actor_id,
        })

    logger.info("Successfully parsed %d speech samples from RAVDESS", len(records))
    return records


def parse_savee(savee_dir: Path) -> List[Dict]:
    """Parse raw SAVEE audio files (format: <actor>_<emotion_code><num>.wav)."""
    records = []
    pattern = re.compile(r"^([A-Z]{2})_([a-z]+)(\d+)\.wav$", re.IGNORECASE)

    wav_files = sorted(list(savee_dir.rglob("*.wav")))
    logger.info("Found %d WAV files in SAVEE folder: %s", len(wav_files), savee_dir)

    actor_map = {"DC": 101, "JE": 102, "JK": 103, "KL": 104}

    for file in wav_files:
        match = pattern.match(file.name)
        if not match:
            continue
        actor_code, emotion_code, num_str = match.groups()
        actor_code = actor_code.upper()
        emotion_code = emotion_code.lower()

        emotion_str = SAVEE_EMOTION_MAP.get(emotion_code)
        if not emotion_str or emotion_str not in LABEL_MAP:
            logger.warning("Unmapped SAVEE emotion code '%s' in file: %s", emotion_code, file.name)
            continue

        records.append({
            "dataset_name": "savee",
            "original_filepath": str(file.resolve()),
            "original_filename": file.name,
            "dest_subpath": f"audio/savee/{actor_code}/savee_{file.name}",
            "emotion": emotion_str,
            "label": LABEL_MAP[emotion_str],
            "actor_id": actor_map.get(actor_code, 999),
        })

    logger.info("Successfully parsed %d samples from SAVEE", len(records))
    return records


def assign_splits(records: List[Dict], seed: int = 42, split_by_actor: bool = True) -> List[Dict]:
    """
    Assign train, val, test splits.
    
    If split_by_actor is True (default & recommended for SER):
      - RAVDESS: Actors 1-16 -> Train | Actors 17-20 -> Val | Actors 21-24 -> Test
      - SAVEE:   Actors 101,102 (DC,JE) -> Train | Actor 103 (JK) -> Val | Actor 104 (KL) -> Test
      This ensures ZERO actor leakage between splits.
    """
    df = pd.DataFrame(records)

    if split_by_actor:
        # Actor-independent split mappings
        ravdess_train = set(range(1, 17))
        ravdess_val = set(range(17, 21))
        ravdess_test = set(range(21, 25))

        savee_train = {101, 102}  # DC, JE
        savee_val = {103}         # JK
        savee_test = {104}        # KL

        df["split"] = ""
        for idx, row in df.iterrows():
            dataset = row["dataset_name"]
            actor = row["actor_id"]

            if dataset == "ravdess":
                if actor in ravdess_train:
                    df.loc[idx, "split"] = "train"
                elif actor in ravdess_val:
                    df.loc[idx, "split"] = "validation"
                elif actor in ravdess_test:
                    df.loc[idx, "split"] = "test"
            elif dataset == "savee":
                if actor in savee_train:
                    df.loc[idx, "split"] = "train"
                elif actor in savee_val:
                    df.loc[idx, "split"] = "validation"
                elif actor in savee_test:
                    df.loc[idx, "split"] = "test"
    else:
        # Sample-level random stratified split by emotion
        rng = np.random.RandomState(seed)
        df["split"] = ""
        for emotion, group in df.groupby("emotion"):
            indices = group.index.tolist()
            rng.shuffle(indices)

            n = len(indices)
            n_train = int(round(0.70 * n))
            n_val = int(round(0.15 * n))

            train_idx = indices[:n_train]
            val_idx = indices[n_train : n_train + n_val]
            test_idx = indices[n_train + n_val :]

            df.loc[train_idx, "split"] = "train"
            df.loc[val_idx, "split"] = "validation"
            df.loc[test_idx, "split"] = "test"

    return df.to_dict("records")


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess and Combine RAVDESS & SAVEE Datasets")
    parser.add_argument(
        "--ravdess_dir",
        type=str,
        default=str(PROJECT_ROOT / "data" / "raw" / "ravdess" if (PROJECT_ROOT / "data" / "raw" / "ravdess").exists() else PROJECT_ROOT / "dataset" / "Audio_Song_Actors_01-24"),
        help="Path to raw RAVDESS dataset directory",
    )
    parser.add_argument(
        "--savee_dir",
        type=str,
        default=str(PROJECT_ROOT / "data" / "raw" / "savee" if (PROJECT_ROOT / "data" / "raw" / "savee").exists() else PROJECT_ROOT / "dataset" / "savee"),
        help="Path to raw SAVEE dataset directory",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(PROJECT_ROOT / "data" / "combined"),
        help="Output directory for preprocessed dataset",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for split reproducibility")
    parser.add_argument("--sample_level", action="store_true", help="Perform random sample-level split instead of actor-independent split")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    audio_out_dir = output_dir / "audio"
    metadata_out_dir = output_dir / "metadata"

    audio_out_dir.mkdir(parents=True, exist_ok=True)
    metadata_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse both datasets
    ravdess_records = parse_ravdess(Path(args.ravdess_dir))
    savee_records = parse_savee(Path(args.savee_dir))

    all_records = ravdess_records + savee_records
    if not all_records:
        logger.error("No valid audio records found.")
        sys.exit(1)

    logger.info("Total audio samples gathered: %d (RAVDESS: %d, SAVEE: %d)", len(all_records), len(ravdess_records), len(savee_records))

    # 2. Assign splits (Actor-Independent by default)
    all_records = assign_splits(all_records, seed=args.seed, split_by_actor=not args.sample_level)

    # 3. Process & Resample Audio Files
    logger.info("Converting and resampling audio files to 16kHz mono PCM WAV...")
    processed_rows = []
    for idx, rec in enumerate(all_records):
        src_path = Path(rec["original_filepath"])
        dest_rel_path = rec["dest_subpath"]
        dest_full_path = output_dir / dest_rel_path

        try:
            duration, sr, channels, audio_hash = process_audio(src_path, dest_full_path)
            row = {
                "filepath": dest_rel_path,
                "original_filepath": str(src_path),
                "filename": dest_full_path.name,
                "emotion": rec["emotion"],
                "label": rec["label"],
                "actor_id": rec["actor_id"],
                "dataset_name": rec["dataset_name"],
                "duration": round(duration, 3),
                "sample_rate": sr,
                "num_channels": channels,
                "split": rec["split"],
                "audio_hash": audio_hash,
            }
            processed_rows.append(row)
        except Exception as e:
            logger.error("Failed processing %s: %s", src_path, e)

    df_all = pd.DataFrame(processed_rows)

    # Save master metadata
    df_all.to_csv(metadata_out_dir / "combined_metadata.csv", index=False)

    # Save splits
    train_df = df_all[df_all["split"] == "train"].reset_index(drop=True)
    val_df = df_all[df_all["split"] == "validation"].reset_index(drop=True)
    test_df = df_all[df_all["split"] == "test"].reset_index(drop=True)

    train_df.to_csv(metadata_out_dir / "train.csv", index=False)
    val_df.to_csv(metadata_out_dir / "validation.csv", index=False)
    test_df.to_csv(metadata_out_dir / "test.csv", index=False)

    total_len = len(df_all)
    logger.info("Preprocessing & Splitting Complete!")
    logger.info("  - Train Split:      %d files (%.1f%%)", len(train_df), (len(train_df) / total_len) * 100)
    logger.info("  - Validation Split: %d files (%.1f%%)", len(val_df), (len(val_df) / total_len) * 100)
    logger.info("  - Test Split:       %d files (%.1f%%)", len(test_df), (len(test_df) / total_len) * 100)


if __name__ == "__main__":
    main()
