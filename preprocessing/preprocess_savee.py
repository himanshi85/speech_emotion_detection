#!/usr/bin/env python3
"""
SAVEE Preprocessing Pipeline
============================
Preprocesses the Surrey Audio-Visual Expressed Emotion (SAVEE) Dataset:
1. Reads all raw audio WAV files from speech_emotion_detection_drive/dataset/savee/.
2. Resamples all audio to 16 kHz, single-channel (mono) PCM 16-bit WAV.
3. Standardizes emotion categories into standard 7-class scheme:
   anger (0), disgust (1), fear (2), happiness (3), neutral (4), sadness (5), surprise (6).
4. Creates actor-independent splits ensuring zero speaker leakage across splits:
   - Train (50%): DC, JE (240 clips)
   - Validation (25%): JK (120 clips)
   - Test (25%): KL (120 clips — unseen during training/validation)
5. Saves all processed files into `savee_preprocessed/` with metadata CSVs and labels.json.
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

# SAVEE emotion code mapping: a=anger, d=disgust, f=fear, h=happiness, n=neutral, sa=sadness, su=surprise
SAVEE_EMOTION_MAP: Dict[str, Tuple[str, int]] = {
    "a": ("anger", 0),
    "d": ("disgust", 1),
    "f": ("fear", 2),
    "h": ("happiness", 3),
    "n": ("neutral", 4),
    "sa": ("sadness", 5),
    "su": ("surprise", 6),
}

LABEL_MAP: Dict[str, int] = {
    "anger": 0,
    "disgust": 1,
    "fear": 2,
    "happiness": 3,
    "neutral": 4,
    "sadness": 5,
    "surprise": 6,
}

# Speaker assignments
ACTOR_CONFIG = {
    "DC": {"actor_id": 1, "split": "train"},
    "JE": {"actor_id": 2, "split": "train"},
    "JK": {"actor_id": 3, "split": "validation"},
    "KL": {"actor_id": 4, "split": "test"},
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("preprocess_savee")


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

    # Convert stereo to mono
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


def parse_savee_filename(filename: str) -> Tuple[str, str, int] | None:
    """
    Parse filename like DC_a01.wav -> (actor_code, emotion_code, sentence_num).
    Actors: DC, JE, JK, KL
    Emotions: a, d, f, h, n, sa, su
    """
    stem = Path(filename).stem
    m = re.match(r"^([A-Z]{2})_([a-z]+)(\d+)$", stem)
    if not m:
        return None
    actor_code, emo_code, sent_num = m.groups()
    if actor_code not in ACTOR_CONFIG or emo_code not in SAVEE_EMOTION_MAP:
        return None
    return actor_code, emo_code, int(sent_num)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preprocess SAVEE speech emotion recognition dataset.")
    default_savee = PROJECT_ROOT / "dataset" / "savee"
    if not default_savee.exists():
        default_savee = PROJECT_ROOT.parent / "speech_emotion_detection_drive" / "dataset" / "savee"
    parser.add_argument(
        "--raw_dir",
        type=str,
        default=str(default_savee),
        help="Directory containing raw SAVEE .wav audio files.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(PROJECT_ROOT / "savee_preprocessed"),
        help="Destination directory for standardized audio and metadata.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    audio_out_dir = output_dir / "audio"
    metadata_out_dir = output_dir / "metadata"

    if not raw_dir.exists():
        logger.error("Raw SAVEE directory not found: %s", raw_dir)
        return 1

    wav_files = sorted(list(raw_dir.glob("*.wav")))
    logger.info("Found %d audio files in %s", len(wav_files), raw_dir)

    if len(wav_files) == 0:
        logger.error("No WAV files found in %s", raw_dir)
        return 1

    metadata_records: List[Dict] = []
    logger.info("Standardizing audio to 16 kHz mono 16-bit PCM...")

    for raw_file in tqdm(wav_files, desc="Processing SAVEE"):
        parsed = parse_savee_filename(raw_file.name)
        if not parsed:
            logger.warning("Skipping unrecognized filename: %s", raw_file.name)
            continue

        actor_code, emo_code, sent_num = parsed
        actor_meta = ACTOR_CONFIG[actor_code]
        emotion_name, emotion_id = SAVEE_EMOTION_MAP[emo_code]

        out_audio_path = audio_out_dir / raw_file.name
        duration, num_samples, file_size, sha256 = process_audio(raw_file, out_audio_path)

        metadata_records.append({
            "filepath": f"audio/{raw_file.name}",
            "filename": raw_file.name,
            "actor_id": actor_meta["actor_id"],
            "actor_code": actor_code,
            "sentence_num": sent_num,
            "emotion": emotion_name,
            "label": emotion_id,
            "sample_rate": TARGET_SAMPLE_RATE,
            "num_channels": TARGET_CHANNELS,
            "duration": round(duration, 4),
            "num_samples": num_samples,
            "file_size": file_size,
            "sha256": sha256,
            "split": actor_meta["split"],
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

    logger.info("==================================================")
    logger.info("SAVEE Preprocessing Complete!")
    logger.info("Output directory: %s", output_dir)
    logger.info("Total clips: %d", len(df))
    logger.info("Train:      %d clips (Actors: DC, JE)", len(train_df))
    logger.info("Validation: %d clips (Actor: JK)", len(val_df))
    logger.info("Test:       %d clips (Actor: KL — UNSEEN)", len(test_df))
    logger.info("==================================================")

    # Print emotion distribution
    print("\nSAVEE Emotion Distribution by Split:")
    dist_table = pd.crosstab(df["emotion"], df["split"], margins=True)
    print(dist_table)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
