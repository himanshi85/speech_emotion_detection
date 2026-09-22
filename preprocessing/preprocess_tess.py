#!/usr/bin/env python3
"""
TESS Preprocessing Pipeline
===========================
Preprocesses the Toronto Emotional Speech Set (TESS) dataset:
1. Reads all 2,800 raw audio WAV files across 14 emotion/actress folders.
2. Standardizes audio to 16 kHz, single-channel (mono) PCM 16-bit WAV.
3. Standardizes emotion categories into standard 7-class scheme:
   angry (0), disgust (1), fear (2), happy (3), neutral (4), pleasant_surprise (5), sad (6).
4. Creates prompt-independent (word-disjoint) splits ensuring zero target word leakage:
   - Train (70%): 140 target words across both actresses (1,960 clips)
   - Validation (15%): 30 target words across both actresses (420 clips)
   - Test (15%): 30 target words across both actresses (420 clips — unseen vocabulary)
5. Saves all processed files into `tess_preprocessed/` with metadata CSVs and labels.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd
import soundfile as sf
from scipy import signal
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1

LABEL_MAP: Dict[str, int] = {
    "angry": 0,
    "disgust": 1,
    "fear": 2,
    "happy": 3,
    "neutral": 4,
    "pleasant_surprise": 5,
    "sad": 6,
}

FOLDER_CONFIG: Dict[str, Tuple[str, str, int]] = {
    "OAF_angry": ("OAF", "angry", 0),
    "OAF_disgust": ("OAF", "disgust", 1),
    "OAF_Fear": ("OAF", "fear", 2),
    "OAF_happy": ("OAF", "happy", 3),
    "OAF_neutral": ("OAF", "neutral", 4),
    "OAF_Pleasant_surprise": ("OAF", "pleasant_surprise", 5),
    "OAF_Sad": ("OAF", "sad", 6),
    "YAF_angry": ("YAF", "angry", 0),
    "YAF_disgust": ("YAF", "disgust", 1),
    "YAF_fear": ("YAF", "fear", 2),
    "YAF_happy": ("YAF", "happy", 3),
    "YAF_neutral": ("YAF", "neutral", 4),
    "YAF_pleasant_surprised": ("YAF", "pleasant_surprise", 5),
    "YAF_sad": ("YAF", "sad", 6),
}

ACTOR_INFO: Dict[str, Dict[str, int | str]] = {
    "OAF": {"actor_id": 1, "age": 64, "gender": "female"},
    "YAF": {"actor_id": 2, "age": 26, "gender": "female"},
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("preprocess_tess")


def compute_audio_hash(filepath: Path) -> str:
    """Compute SHA256 hash of file content."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def process_audio(input_path: Path, output_path: Path) -> Tuple[float, int, int, str]:
    """Read, convert to mono 16kHz PCM WAV, and save to output_path."""
    audio_data, sr = sf.read(str(input_path), dtype="float32")

    # Convert stereo to mono if needed
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Resample if needed
    if sr != TARGET_SAMPLE_RATE:
        num_target_samples = int(round(len(audio_data) * TARGET_SAMPLE_RATE / sr))
        audio_data = signal.resample(audio_data, num_target_samples)

    # Normalize audio level to prevent clipping
    peak = np.max(np.abs(audio_data))
    if peak > 1.0:
        audio_data = audio_data / peak

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio_data, TARGET_SAMPLE_RATE, subtype="PCM_16")

    duration = len(audio_data) / TARGET_SAMPLE_RATE
    num_samples = len(audio_data)
    file_size = output_path.stat().st_size
    file_hash = compute_audio_hash(output_path)

    return duration, num_samples, file_size, file_hash


def extract_word_from_stem(stem: str) -> str:
    """Extract target word from filename stem e.g. OAF_back_angry -> back."""
    parts = stem.split("_")
    if len(parts) >= 2:
        return parts[1].lower()
    return stem.lower()


def main() -> int:
    default_raw = (
        Path.home()
        / ".cache"
        / "kagglehub"
        / "datasets"
        / "ejlok1"
        / "toronto-emotional-speech-set-tess"
        / "versions"
        / "1"
        / "TESS Toronto emotional speech set data"
    )

    parser = argparse.ArgumentParser(description="Preprocess TESS speech emotion recognition dataset.")
    parser.add_argument(
        "--raw_dir",
        type=str,
        default=str(default_raw),
        help="Directory containing raw TESS audio folders.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(PROJECT_ROOT / "tess_preprocessed"),
        help="Destination directory for standardized audio and metadata.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for word-disjoint train/val/test partition.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    audio_out_dir = output_dir / "audio"
    metadata_out_dir = output_dir / "metadata"

    if not raw_dir.exists():
        logger.error("Raw TESS directory not found: %s", raw_dir)
        return 1

    # Locate the 14 emotion folders
    matched_folders = {}
    for folder_name, meta in FOLDER_CONFIG.items():
        p = raw_dir / folder_name
        if p.is_dir():
            matched_folders[folder_name] = (p, meta)
        else:
            # Check if nested
            nested = list(raw_dir.glob(f"**/{folder_name}"))
            if nested and nested[0].is_dir():
                matched_folders[folder_name] = (nested[0], meta)

    if len(matched_folders) != 14:
        logger.error("Expected 14 emotion folders, found %d in %s", len(matched_folders), raw_dir)
        return 1

    logger.info("Found all 14 emotion folders in %s", raw_dir)

    # First pass: collect all files and unique words
    raw_files_info = []
    all_words_set: Set[str] = set()

    for folder_name, (folder_path, (speaker, emotion, label_id)) in sorted(matched_folders.items()):
        wav_files = sorted(list(folder_path.glob("*.wav")))
        if len(wav_files) != 200:
            logger.warning("Folder %s has %d files (expected 200)", folder_name, len(wav_files))
        for wav_path in wav_files:
            word = extract_word_from_stem(wav_path.stem)
            all_words_set.add(word)
            raw_files_info.append((wav_path, speaker, emotion, label_id, word))

    logger.info("Total clips found: %d across %d distinct target words.", len(raw_files_info), len(all_words_set))
    if len(all_words_set) != 200:
        logger.error("Expected exactly 200 target words, found %d", len(all_words_set))
        return 1

    # Deterministic word-disjoint split: 140 train (70%), 30 val (15%), 30 test (15%)
    sorted_words = sorted(list(all_words_set))
    rng = np.random.RandomState(args.seed)
    permuted_words = rng.permutation(sorted_words)
    train_words = set(permuted_words[:140])
    val_words = set(permuted_words[140:170])
    test_words = set(permuted_words[170:])

    assert len(train_words) == 140
    assert len(val_words) == 30
    assert len(test_words) == 30
    assert len(train_words & val_words) == 0
    assert len(train_words & test_words) == 0
    assert len(val_words & test_words) == 0
    logger.info("Partitioned 200 target words: 140 Train, 30 Val, 30 Test (Zero word leakage).")

    # Second pass: standardize audio and write metadata
    logger.info("Standardizing audio to 16 kHz mono 16-bit PCM...")
    metadata_records: List[Dict] = []

    for wav_path, speaker, emotion, label_id, word in tqdm(raw_files_info, desc="Processing TESS"):
        # Determine split
        if word in train_words:
            split = "train"
        elif word in val_words:
            split = "validation"
        else:
            split = "test"

        # Standardized filename e.g. OAF_back_angry.wav
        standard_filename = f"{speaker}_{word}_{emotion}.wav"
        out_audio_path = audio_out_dir / standard_filename
        duration, num_samples, file_size, sha256 = process_audio(wav_path, out_audio_path)

        metadata_records.append({
            "filepath": f"audio/{standard_filename}",
            "filename": standard_filename,
            "actor_id": ACTOR_INFO[speaker]["actor_id"],
            "actor_code": speaker,
            "word": word,
            "emotion": emotion,
            "label": label_id,
            "sample_rate": TARGET_SAMPLE_RATE,
            "num_channels": TARGET_CHANNELS,
            "duration": round(duration, 4),
            "num_samples": num_samples,
            "file_size": file_size,
            "sha256": sha256,
            "split": split,
        })

    df = pd.DataFrame(metadata_records)
    logger.info("Successfully processed %d valid audio files.", len(df))

    # Save metadata splits
    metadata_out_dir.mkdir(parents=True, exist_ok=True)
    train_df = df[df["split"] == "train"].reset_index(drop=True)
    val_df = df[df["split"] == "validation"].reset_index(drop=True)
    test_df = df[df["split"] == "test"].reset_index(drop=True)

    df.to_csv(metadata_out_dir / "full_metadata.csv", index=False)
    train_df.to_csv(metadata_out_dir / "train.csv", index=False)
    val_df.to_csv(metadata_out_dir / "validation.csv", index=False)
    test_df.to_csv(metadata_out_dir / "test.csv", index=False)

    # Save labels.json
    (metadata_out_dir / "labels.json").write_text(
        json.dumps(LABEL_MAP, indent=2), encoding="utf-8"
    )

    # Save word split record for verification and audit
    word_splits = {
        "train_words": sorted(list(train_words)),
        "validation_words": sorted(list(val_words)),
        "test_words": sorted(list(test_words)),
    }
    (metadata_out_dir / "word_splits.json").write_text(
        json.dumps(word_splits, indent=2), encoding="utf-8"
    )

    logger.info("==================================================")
    logger.info("TESS Preprocessing Complete!")
    logger.info("Output directory: %s", output_dir)
    logger.info("Total clips: %d", len(df))
    logger.info("Train:      %d clips (140 words x 2 actresses x 7 emotions)", len(train_df))
    logger.info("Validation: %d clips (30 words x 2 actresses x 7 emotions)", len(val_df))
    logger.info("Test:       %d clips (30 words x 2 actresses x 7 emotions — UNSEEN)", len(test_df))
    logger.info("==================================================")

    # Print emotion distribution
    print("\nTESS Emotion Distribution by Split:")
    dist_table = pd.crosstab(df["emotion"], df["split"], margins=True)
    print(dist_table)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
