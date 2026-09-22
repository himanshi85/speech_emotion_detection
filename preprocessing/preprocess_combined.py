#!/usr/bin/env python3
"""
Multi-Corpus Combined SER Preprocessing Pipeline
=================================================
Unifies all 4 Speech Emotion Recognition datasets (CREMA-D, RAVDESS, SAVEE, TESS)
into a single, standardized, zero-leakage multi-corpus dataset:
- Standardized to the 6 Core Canonical Emotions: neutral, happy, sad, angry, fear, disgust.
- Preserves all established unseen test actor / prompt splits (zero speaker & prompt leakage).
- Standardized audio references with zero disk duplication via relative symlinks.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("preprocess_combined")

# Canonical 6 Emotion Schema
CANONICAL_LABELS = {
    "neutral": 0,
    "happy": 1,
    "sad": 2,
    "angry": 3,
    "fear": 4,
    "disgust": 5,
}

# Emotion Mappings to Canonical
EMOTION_MAPPINGS = {
    "cremad": {
        "neutral": "neutral",
        "happy": "happy",
        "sad": "sad",
        "angry": "angry",
        "fearful": "fear",
        "disgust": "disgust",
    },
    "ravdess": {
        "neutral": "neutral",
        "happy": "happy",
        "sad": "sad",
        "angry": "angry",
        "fearful": "fear",
        "disgust": "disgust",
        # "calm" and "surprised" excluded to preserve pure 6-class taxonomy
    },
    "savee": {
        "neutral": "neutral",
        "happiness": "happy",
        "sadness": "sad",
        "anger": "angry",
        "fear": "fear",
        "disgust": "disgust",
        # "surprise" excluded
    },
    "tess": {
        "neutral": "neutral",
        "happy": "happy",
        "sad": "sad",
        "angry": "angry",
        "fear": "fear",
        "disgust": "disgust",
        # "pleasant_surprise" excluded
    },
}

SAVEE_ACTOR_MAP = {"DC": 2001, "JE": 2002, "JK": 2003, "KL": 2004}
TESS_ACTOR_MAP = {"OAF": 3001, "YAF": 3002}


def process_dataset(
    dataset_name: str,
    preprocessed_dir: Path,
    combined_audio_dir: Path,
) -> pd.DataFrame:
    meta_csv = preprocessed_dir / "metadata" / "full_metadata.csv"
    if not meta_csv.exists():
        if dataset_name == "ravdess":
            meta_csv = preprocessed_dir / "metadata" / "ravdess_metadata.csv"
        else:
            raise FileNotFoundError(f"Metadata file not found: {meta_csv}")

    df = pd.read_csv(meta_csv)
    mapping = EMOTION_MAPPINGS[dataset_name]

    # Filter to valid canonical emotions
    df["raw_emotion"] = df["emotion"].astype(str).str.lower()
    df = df[df["raw_emotion"].isin(mapping.keys())].copy()
    df["canonical_emotion"] = df["raw_emotion"].map(mapping)
    df["label"] = df["canonical_emotion"].map(CANONICAL_LABELS)
    df["dataset"] = dataset_name

    # Namespace actor IDs
    if dataset_name == "savee":
        if "speaker" in df.columns:
            df["actor_id"] = df["speaker"].map(SAVEE_ACTOR_MAP).fillna(2000).astype(int)
        else:
            df["actor_id"] = df["actor_id"] + 2000
    elif dataset_name == "tess":
        if "speaker" in df.columns:
            df["actor_id"] = df["speaker"].map(TESS_ACTOR_MAP).fillna(3000).astype(int)
        else:
            df["actor_id"] = df["actor_id"] + 3000
    elif dataset_name == "ravdess":
        df["actor_id"] = df["actor_id"].astype(int)
    elif dataset_name == "cremad":
        df["actor_id"] = df["actor_id"].astype(int)

    # Resolve relative filepath under combined_preprocessed/audio/<dataset>/...
    # Create symlink for audio directory if not present
    ds_audio_link = combined_audio_dir / dataset_name
    src_audio = preprocessed_dir / "audio"
    if not ds_audio_link.exists():
        rel_target = os.path.relpath(src_audio, combined_audio_dir)
        ds_audio_link.symlink_to(rel_target, target_is_directory=True)
        logger.info("Created audio symlink: %s -> %s", ds_audio_link, rel_target)

    # Format filepath column: audio/<dataset>/<original_subpath>
    # In ravdess: audio/Actor_01/... -> audio/ravdess/Actor_01/...
    # In cremad: audio/1001_... -> audio/cremad/1001_...
    def adjust_filepath(fp: str) -> str:
        p = str(fp)
        if p.startswith("audio/"):
            p = p[len("audio/"):]
        return f"audio/{dataset_name}/{p}"

    df["filepath"] = df["filepath"].apply(adjust_filepath)
    df["emotion"] = df["canonical_emotion"]

    logger.info("Processed %s: %d clips across %d actors",
                dataset_name.upper(), len(df), df["actor_id"].nunique())
    return df


def main() -> int:
    combined_dir = PROJECT_ROOT / "combined_preprocessed"
    combined_audio = combined_dir / "audio"
    combined_meta = combined_dir / "metadata"

    combined_dir.mkdir(parents=True, exist_ok=True)
    combined_audio.mkdir(parents=True, exist_ok=True)
    combined_meta.mkdir(parents=True, exist_ok=True)

    datasets = {
        "cremad": PROJECT_ROOT / "cremad_preprocessed",
        "ravdess": PROJECT_ROOT / "ravdess_preprocessed",
        "savee": PROJECT_ROOT / "savee_preprocessed",
        "tess": PROJECT_ROOT / "tess_preprocessed",
    }

    all_dfs = []
    for dname, dpath in datasets.items():
        if not dpath.exists():
            logger.error("Required dataset directory not found: %s", dpath)
            return 1
        df = process_dataset(dname, dpath, combined_audio)
        all_dfs.append(df)

    full_df = pd.concat(all_dfs, ignore_index=True)

    # Standardize column selection
    columns = [
        "filepath",
        "filename",
        "emotion",
        "label",
        "actor_id",
        "sample_rate",
        "num_channels",
        "duration",
        "split",
        "dataset",
    ]
    # Ensure all required columns exist
    for col in columns:
        if col not in full_df.columns:
            if col == "sample_rate":
                full_df[col] = 16000
            elif col == "num_channels":
                full_df[col] = 1
            elif col == "duration":
                full_df[col] = 3.0

    full_df = full_df[columns]

    # Partition by split
    train_df = full_df[full_df["split"] == "train"].reset_index(drop=True)
    val_df = full_df[full_df["split"] == "validation"].reset_index(drop=True)
    test_df = full_df[full_df["split"] == "test"].reset_index(drop=True)

    # Save CSVs
    full_df.to_csv(combined_meta / "full_metadata.csv", index=False)
    train_df.to_csv(combined_meta / "train.csv", index=False)
    val_df.to_csv(combined_meta / "validation.csv", index=False)
    test_df.to_csv(combined_meta / "test.csv", index=False)

    # Save labels.json
    (combined_meta / "labels.json").write_text(json.dumps(CANONICAL_LABELS, indent=2), encoding="utf-8")

    # Summary
    summary = {
        "total_clips": len(full_df),
        "total_actors": int(full_df["actor_id"].nunique()),
        "splits": {
            "train": len(train_df),
            "validation": len(val_df),
            "test": len(test_df),
        },
        "datasets": {d: int((full_df["dataset"] == d).sum()) for d in datasets.keys()},
        "emotions": {e: int((full_df["emotion"] == e).sum()) for e in CANONICAL_LABELS.keys()},
        "dataset_split_matrix": full_df.groupby(["dataset", "split"]).size().unstack(fill_value=0).to_dict(),
    }
    (combined_meta / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    logger.info("==================================================")
    logger.info("🎉 Combined Multi-Corpus Preprocessing Complete!")
    logger.info("Total Clips:     %d", len(full_df))
    logger.info("Total Actors:    %d", full_df["actor_id"].nunique())
    logger.info("Train Clips:     %d (%0.1f%%)", len(train_df), 100 * len(train_df) / len(full_df))
    logger.info("Val Clips:       %d (%0.1f%%)", len(val_df), 100 * len(val_df) / len(full_df))
    logger.info("Test Clips:      %d (%0.1f%%)", len(test_df), 100 * len(test_df) / len(full_df))
    logger.info("==================================================")

    # Print distribution
    print("\nDataset & Split Matrix:")
    print(full_df.groupby(["dataset", "split"]).size().unstack(fill_value=0))
    print("\nCanonical Emotion Distribution:")
    print(full_df["emotion"].value_counts())
    print("\nSaved to:", combined_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
