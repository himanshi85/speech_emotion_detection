#!/usr/bin/env python3
"""
CREMA-D Preprocessing Pipeline
==============================
Preprocesses the Crowd-sourced Emotional Multimodal Actors Dataset (CREMA-D):
1. Reads all raw audio WAV files from AudioWAV/.
2. Resamples all audio to 16 kHz, single-channel (mono) PCM 16-bit WAV.
3. Standardizes emotion categories into standard 6-class scheme:
   neutral (0), happy (1), sad (2), angry (3), fearful (4), disgust (5).
4. Creates actor-independent splits (70% Train, 15% Validation, 15% Test)
   ensuring zero speaker leakage across splits.
5. Saves all processed files into `cremad_preprocessed/` with metadata CSVs and labels.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
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

CREMA_EMOTION_MAP: Dict[str, Tuple[str, int]] = {
    "NEU": ("neutral", 0),
    "HAP": ("happy", 1),
    "SAD": ("sad", 2),
    "ANG": ("angry", 3),
    "FEA": ("fearful", 4),
    "DIS": ("disgust", 5),
}

LABEL_MAP: Dict[str, int] = {
    "neutral": 0,
    "happy": 1,
    "sad": 2,
    "angry": 3,
    "fearful": 4,
    "disgust": 5,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("preprocess_cremad")


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

    # Resample to 16 kHz if necessary
    if sr != TARGET_SAMPLE_RATE:
        gcd_val = math.gcd(TARGET_SAMPLE_RATE, int(sr))
        up = TARGET_SAMPLE_RATE // gcd_val
        down = int(sr) // gcd_val
        audio_data = signal.resample_poly(audio_data, up, down)
        sr = TARGET_SAMPLE_RATE

    duration = float(len(audio_data)) / float(TARGET_SAMPLE_RATE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio_data, TARGET_SAMPLE_RATE, subtype="PCM_16")

    audio_hash = compute_audio_hash(output_path)
    return duration, TARGET_SAMPLE_RATE, TARGET_CHANNELS, audio_hash


def parse_cremad_filename(filename: str) -> Dict[str, str]:
    """
    Parse CREMA-D filename into constituent metadata.
    Example: 1001_DFA_ANG_XX.wav -> actor=1001, sentence=DFA, emotion=ANG, intensity=XX
    """
    stem = Path(filename).stem
    parts = stem.split("_")
    if len(parts) != 4:
        raise ValueError(f"Unexpected CREMA-D filename structure: {filename}")
    actor_str, sentence, emotion_code, intensity = parts
    return {
        "actor_id": int(actor_str),
        "sentence": sentence,
        "emotion_code": emotion_code,
        "intensity": intensity,
    }


def split_actors_independent(
    actors: List[int],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> Tuple[Set[int], Set[int], Set[int]]:
    """Partition unique actors into disjoint train, val, test sets."""
    rng = np.random.default_rng(seed)
    shuffled = sorted(actors)
    rng.shuffle(shuffled)

    n_total = len(shuffled)
    n_train = int(round(n_total * train_ratio))
    n_val = int(round(n_total * val_ratio))

    train_actors = set(shuffled[:n_train])
    val_actors = set(shuffled[n_train : n_train + n_val])
    test_actors = set(shuffled[n_train + n_val :])

    # Assert zero actor leakage
    assert len(train_actors & val_actors) == 0, "Actor leakage train ∩ val!"
    assert len(train_actors & test_actors) == 0, "Actor leakage train ∩ test!"
    assert len(val_actors & test_actors) == 0, "Actor leakage val ∩ test!"
    assert len(train_actors) + len(val_actors) + len(test_actors) == n_total

    return train_actors, val_actors, test_actors


def main() -> int:
    parser = argparse.ArgumentParser(description="Preprocess CREMA-D dataset")
    parser.add_argument(
        "--input_dir",
        type=str,
        default=os.path.expanduser(
            "~/.cache/kagglehub/datasets/ejlok1/cremad/versions/1/AudioWAV"
        ),
        help="Path to raw AudioWAV folder",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="cremad_preprocessed",
        help="Path to preprocessed output directory",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for actor split")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not input_dir.exists():
        # Check alternate known paths
        candidates = [
            PROJECT_ROOT / "dataset" / "crema_d",
            PROJECT_ROOT / "dataset" / "cremad",
            Path.home() / "Downloads" / "crema-d",
        ]
        for c in candidates:
            if c.exists():
                input_dir = c.resolve()
                break

    if not input_dir.exists():
        logger.error("Input directory not found: %s", input_dir)
        return 1

    audio_files = sorted(list(input_dir.glob("*.wav")))
    if not audio_files:
        # Check subdirectories
        audio_files = sorted(list(input_dir.glob("**/*.wav")))

    logger.info("Found %d audio files in %s", len(audio_files), input_dir)
    if len(audio_files) == 0:
        logger.error("No WAV files found.")
        return 1

    out_audio_dir = output_dir / "audio"
    out_meta_dir = output_dir / "metadata"
    out_audio_dir.mkdir(parents=True, exist_ok=True)
    out_meta_dir.mkdir(parents=True, exist_ok=True)

    # Collect actors
    parsed_items = []
    actor_set = set()
    for af in audio_files:
        try:
            info = parse_cremad_filename(af.name)
            if info["emotion_code"] not in CREMA_EMOTION_MAP:
                logger.warning("Skipping unknown emotion code: %s", af.name)
                continue
            actor_set.add(info["actor_id"])
            parsed_items.append((af, info))
        except Exception as e:
            logger.warning("Error parsing %s: %s", af.name, e)

    unique_actors = sorted(list(actor_set))
    logger.info("Identified %d unique actors: %d to %d", len(unique_actors), min(unique_actors), max(unique_actors))

    train_actors, val_actors, test_actors = split_actors_independent(unique_actors, seed=args.seed)
    logger.info(
        "Actor Partition: Train=%d actors, Val=%d actors, Test=%d actors (Total=%d)",
        len(train_actors),
        len(val_actors),
        len(test_actors),
        len(unique_actors),
    )

    rows = []
    for af, info in tqdm(parsed_items, desc="Preprocessing CREMA-D"):
        actor_id = info["actor_id"]
        emotion_name, label_id = CREMA_EMOTION_MAP[info["emotion_code"]]

        if actor_id in train_actors:
            split_name = "train"
        elif actor_id in val_actors:
            split_name = "validation"
        else:
            split_name = "test"

        dst_wav = out_audio_dir / af.name
        rel_filepath = f"audio/{af.name}"

        # Convert and save audio
        duration, sr, channels, audio_hash = process_audio(af, dst_wav)

        rows.append(
            {
                "filepath": rel_filepath,
                "filename": af.name,
                "emotion": emotion_name,
                "label": label_id,
                "actor_id": actor_id,
                "sentence": info["sentence"],
                "intensity": info["intensity"],
                "sample_rate": sr,
                "num_channels": channels,
                "duration": duration,
                "split": split_name,
                "audio_hash": audio_hash,
            }
        )

    df_full = pd.DataFrame(rows)
    df_train = df_full[df_full["split"] == "train"].reset_index(drop=True)
    df_val = df_full[df_full["split"] == "validation"].reset_index(drop=True)
    df_test = df_full[df_full["split"] == "test"].reset_index(drop=True)

    # Save CSVs
    df_full.to_csv(out_meta_dir / "full_metadata.csv", index=False)
    df_train.to_csv(out_meta_dir / "train.csv", index=False)
    df_val.to_csv(out_meta_dir / "validation.csv", index=False)
    df_test.to_csv(out_meta_dir / "test.csv", index=False)

    # Save labels.json
    (out_meta_dir / "labels.json").write_text(json.dumps(LABEL_MAP, indent=2), encoding="utf-8")

    # Save summary
    summary = {
        "dataset": "CREMA-D",
        "num_classes": len(LABEL_MAP),
        "total_clips": len(df_full),
        "train_clips": len(df_train),
        "validation_clips": len(df_val),
        "test_clips": len(df_test),
        "unique_actors": len(unique_actors),
        "train_actors": sorted(list(train_actors)),
        "validation_actors": sorted(list(val_actors)),
        "test_actors": sorted(list(test_actors)),
        "label_mapping": LABEL_MAP,
        "emotion_distribution": {
            "train": df_train["emotion"].value_counts().to_dict(),
            "validation": df_val["emotion"].value_counts().to_dict(),
            "test": df_test["emotion"].value_counts().to_dict(),
        },
    }
    (out_meta_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    logger.info("==========================================")
    logger.info("CREMA-D Preprocessing Complete!")
    logger.info("Total clips: %d", len(df_full))
    logger.info("Train:       %d clips (%d actors)", len(df_train), len(train_actors))
    logger.info("Validation:  %d clips (%d actors)", len(df_val), len(val_actors))
    logger.info("Test:        %d clips (%d actors)", len(df_test), len(test_actors))
    logger.info("Saved to:    %s", output_dir)
    logger.info("==========================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
