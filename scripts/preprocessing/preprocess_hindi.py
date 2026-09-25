#!/usr/bin/env python3
"""
Hindi Speech Emotion Recognition (SER) Preprocessing Pipeline
=============================================================
Ingests, standardizes, and splits Hindi speech emotion corpora:
1. Sources:
   - Project Vaani Indian Speech Corpus (ghostieee11/vaani-speech-corpus)
   - Indian TTS Emotion Corpus (sarthwa8/indian-tts-emotion-60min)
   - Audio Emotion Detection Dataset (RapidOrc121/audio-emotion-detection-dataset)
2. Audio Standardization:
   - 16 kHz sample rate, single-channel (mono), PCM 16-bit WAV.
   - Slices long speech utterances into optimal 4-10 second speech segments.
3. Canonical Emotion Mapping (5 Classes):
   - neutral (0): neutral, formal, serious
   - calm (1): calm
   - happy (2): happy, excited
   - sad (3): sad
   - angry (4): angry
4. Disjoint Train / Validation / Test Splitting:
   - Stratified partition: ~70% Train, ~15% Validation, ~15% Test.
5. Saves artifacts into data/hindi/audio/ and data/hindi/metadata/.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import soundfile as sf
from huggingface_hub import hf_hub_download
from scipy import signal
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("preprocess_hindi")

TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1

LABEL_MAP: Dict[str, int] = {
    "neutral": 0,
    "calm": 1,
    "happy": 2,
    "sad": 3,
    "angry": 4,
}

RAW_EMOTION_MAPPING: Dict[str, str] = {
    "neutral": "neutral",
    "formal": "neutral",
    "serious": "neutral",
    "calm": "calm",
    "happy": "happy",
    "excited": "happy",
    "sad": "sad",
    "angry": "angry",
}


def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for p in [current] + list(current.parents):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _find_project_root()


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    if audio.ndim > 1:
        audio = np.mean(audio, axis=-1)
    if orig_sr == target_sr:
        return audio.astype(np.float32)
    gcd = math.gcd(int(orig_sr), int(target_sr))
    up = target_sr // gcd
    down = orig_sr // gcd
    resampled = signal.resample_poly(audio, up, down)
    return resampled.astype(np.float32)


def segment_audio(
    audio: np.ndarray,
    sr: int,
    min_sec: float = 3.0,
    max_sec: float = 8.0,
    overlap_sec: float = 1.0,
) -> List[np.ndarray]:
    duration = len(audio) / sr
    if duration < min_sec:
        return []
    if duration <= max_sec:
        return [audio]

    step_samples = int((max_sec - overlap_sec) * sr)
    window_samples = int(max_sec * sr)
    segments = []
    for start in range(0, len(audio), step_samples):
        end = start + window_samples
        seg = audio[start:end]
        if len(seg) >= int(min_sec * sr):
            segments.append(seg)
    return segments


def collect_vaani_clips() -> List[Dict]:
    logger.info("Loading ghostieee11/vaani-speech-corpus...")
    pq_path = hf_hub_download(
        repo_id="ghostieee11/vaani-speech-corpus",
        filename="data/train-00000-of-00001.parquet",
        repo_type="dataset",
    )
    df = pd.read_parquet(pq_path)
    hindi_df = df[df["language"] == "hi"]
    logger.info("Found %d Hindi clips in Vaani corpus.", len(hindi_df))

    clips = []
    for idx, row in hindi_df.iterrows():
        raw_emotion = str(row["emotion"]).strip().lower()
        if raw_emotion not in RAW_EMOTION_MAPPING:
            continue
        canonical = RAW_EMOTION_MAPPING[raw_emotion]
        speaker = str(row.get("speaker_id", f"vaani_{idx}"))
        audio_dict = row["audio"]
        raw_bytes = audio_dict["bytes"]
        try:
            arr, sr = sf.read(io.BytesIO(raw_bytes))
            clips.append({
                "source": "vaani",
                "audio": arr,
                "sr": sr,
                "emotion": canonical,
                "speaker": speaker,
                "id": f"vaani_{idx}",
            })
        except Exception as e:
            logger.warning("Error reading Vaani clip %d: %s", idx, e)
    return clips


def collect_sarthwa_clips() -> List[Dict]:
    logger.info("Loading sarthwa8/indian-tts-emotion-60min...")
    pq_path = hf_hub_download(
        repo_id="sarthwa8/indian-tts-emotion-60min",
        filename="data/train-00000-of-00001.parquet",
        repo_type="dataset",
    )
    df = pd.read_parquet(pq_path)
    hindi_df = df[df["language"] == "hi-IN"]
    logger.info("Found %d Hindi clips in sarthwa8 corpus.", len(hindi_df))

    clips = []
    for idx, row in hindi_df.iterrows():
        raw_emotion = str(row["emotion"]).strip().lower()
        if raw_emotion not in RAW_EMOTION_MAPPING:
            continue
        canonical = RAW_EMOTION_MAPPING[raw_emotion]
        speaker = str(row.get("speaker_id", f"sarthwa_{idx}"))
        audio_dict = row["audio"]
        raw_bytes = audio_dict["bytes"]
        try:
            arr, sr = sf.read(io.BytesIO(raw_bytes))
            clips.append({
                "source": "sarthwa8",
                "audio": arr,
                "sr": sr,
                "emotion": canonical,
                "speaker": speaker,
                "id": f"sarthwa_{idx}",
            })
        except Exception as e:
            logger.warning("Error reading sarthwa8 clip %d: %s", idx, e)
    return clips


def collect_rapidorc_clips() -> List[Dict]:
    logger.info("Loading RapidOrc121/audio-emotion-detection-dataset...")
    meta_path = hf_hub_download(
        repo_id="RapidOrc121/audio-emotion-detection-dataset",
        filename="metadata.csv",
        repo_type="dataset",
    )
    df = pd.read_csv(meta_path)
    hindi_df = df[df["language"] == "hindi"]
    logger.info("Found %d Hindi clips in RapidOrc corpus.", len(hindi_df))

    clips = []
    for idx, row in hindi_df.iterrows():
        raw_emotion = str(row["emotion"]).strip().lower()
        if raw_emotion not in RAW_EMOTION_MAPPING:
            continue
        canonical = RAW_EMOTION_MAPPING[raw_emotion]
        fname = str(row["file_name"])
        try:
            wav_path = hf_hub_download(
                repo_id="RapidOrc121/audio-emotion-detection-dataset",
                filename=fname,
                repo_type="dataset",
            )
            arr, sr = sf.read(wav_path)
            clips.append({
                "source": "rapidorc",
                "audio": arr,
                "sr": sr,
                "emotion": canonical,
                "speaker": f"rapidorc_spk_{idx % 5}",
                "id": f"rapidorc_{fname.replace('.wav', '')}",
            })
        except Exception as e:
            logger.warning("Error loading RapidOrc clip %s: %s", fname, e)
    return clips


def main():
    parser = argparse.ArgumentParser(description="Preprocess Hindi Speech Emotion Dataset")
    parser.add_argument("--output_dir", type=str, default="data/hindi", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting")
    args = parser.parse_args()

    np.random.seed(args.seed)

    output_dir = PROJECT_ROOT / args.output_dir
    audio_dir = output_dir / "audio"
    metadata_dir = output_dir / "metadata"
    audio_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # 1. Collect all raw clips
    raw_clips = []
    raw_clips.extend(collect_vaani_clips())
    raw_clips.extend(collect_sarthwa_clips())
    raw_clips.extend(collect_rapidorc_clips())

    logger.info("Total raw Hindi speech clips gathered: %d", len(raw_clips))

    # 2. Process and standardize audio into 16 kHz segments
    records = []
    clip_counter = 0

    logger.info("Standardizing audio to 16 kHz mono PCM 16-bit...")
    for item in tqdm(raw_clips, desc="Processing Audio"):
        resampled = resample_audio(item["audio"], orig_sr=item["sr"], target_sr=TARGET_SAMPLE_RATE)
        segments = segment_audio(resampled, sr=TARGET_SAMPLE_RATE, min_sec=2.5, max_sec=8.0)

        for s_idx, seg in enumerate(segments):
            clip_counter += 1
            out_filename = f"hindi_{clip_counter:05d}.wav"
            out_path = audio_dir / out_filename
            rel_path = f"data/hindi/audio/{out_filename}"

            # Save as 16-bit PCM WAV
            sf.write(str(out_path), seg, TARGET_SAMPLE_RATE, subtype="PCM_16")

            duration = len(seg) / TARGET_SAMPLE_RATE
            emotion = item["emotion"]
            label_id = LABEL_MAP[emotion]

            records.append({
                "filepath": f"audio/{out_filename}",
                "filename": out_filename,
                "emotion": emotion,
                "label": label_id,
                "actor_id": item["speaker"],
                "sample_rate": TARGET_SAMPLE_RATE,
                "num_channels": TARGET_CHANNELS,
                "duration": round(duration, 3),
                "dataset": "hindi",
                "source": item["source"],
            })

    df = pd.DataFrame(records)
    logger.info("Successfully generated %d standardized Hindi speech clips!", len(df))
    logger.info("Emotion Class Distribution:\n%s", df["emotion"].value_counts())

    # 3. Create stratified splits (70% Train, 15% Validation, 15% Test)
    train_rows = []
    val_rows = []
    test_rows = []

    for emotion, group in df.groupby("emotion"):
        shuffled = group.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
        n = len(shuffled)
        n_train = int(round(0.70 * n))
        n_val = int(round(0.15 * n))
        if n_train + n_val >= n:
            n_train = max(1, n - 2)
            n_val = 1

        train_part = shuffled.iloc[:n_train].copy()
        train_part["split"] = "train"
        val_part = shuffled.iloc[n_train:n_train + n_val].copy()
        val_part["split"] = "validation"
        test_part = shuffled.iloc[n_train + n_val:].copy()
        test_part["split"] = "test"

        train_rows.append(train_part)
        val_rows.append(val_part)
        test_rows.append(test_part)

    train_df = pd.concat(train_rows).sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    val_df = pd.concat(val_rows).sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    test_df = pd.concat(test_rows).sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    full_df = pd.concat([train_df, val_df, test_df], ignore_index=True)

    # Save CSVs
    train_df.to_csv(metadata_dir / "train.csv", index=False)
    val_df.to_csv(metadata_dir / "val.csv", index=False)
    val_df.to_csv(metadata_dir / "validation.csv", index=False)
    test_df.to_csv(metadata_dir / "test.csv", index=False)
    full_df.to_csv(metadata_dir / "full_metadata.csv", index=False)

    # Save labels.json
    with open(metadata_dir / "labels.json", "w") as f:
        json.dump(LABEL_MAP, f, indent=2)

    # Save summary
    summary = {
        "dataset": "hindi",
        "num_classes": len(LABEL_MAP),
        "total_clips": len(df),
        "total_duration_hours": round(df["duration"].sum() / 3600.0, 3),
        "sample_rate": TARGET_SAMPLE_RATE,
        "classes": LABEL_MAP,
        "class_distribution": df["emotion"].value_counts().to_dict(),
        "splits": {
            "train": len(train_df),
            "validation": len(val_df),
            "test": len(test_df),
        },
    }
    with open(metadata_dir / "dataset_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("Metadata saved to %s", metadata_dir)
    logger.info("Summary: %s", json.dumps(summary, indent=2))
    print("\nHindi Preprocessing Complete!")
    print(f"Total Clips: {len(df)} | Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")


if __name__ == "__main__":
    main()
