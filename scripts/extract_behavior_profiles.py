"""
Extract empirical acoustic prosody profiles across the evaluation dataset.
Computes speaking rate, pause ratio, vocal energy (RMS dB), and pitch F0 via pYIN.
Outputs:
- outputs/behavior/test_behavior_telemetry.csv (clip-level measurements)
- outputs/behavior/emotion_profiles.csv (corpus/emotion-level empirical aggregations)
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ser.features.behavior import extract_acoustic_prosody, load_audio_robust

def main():
    metadata_path = PROJECT_ROOT / "data" / "hindi" / "metadata" / "test.csv"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Evaluation metadata not found: {metadata_path}")

    df_meta = pd.read_csv(metadata_path)
    out_dir = PROJECT_ROOT / "outputs" / "behavior"
    out_dir.mkdir(parents=True, exist_ok=True)

    records = []
    print(f"Extracting empirical behavioural prosody for {len(df_meta)} evaluation clips...")
    for idx, row in df_meta.iterrows():
        audio_path = PROJECT_ROOT / "data" / "hindi" / row["filepath"]
        audio, sr = load_audio_robust(audio_path, target_sr=16000)
        p = extract_acoustic_prosody(audio, sr=sr)
        records.append({
            "filename": row["filename"],
            "emotion": row["emotion"].capitalize(),
            "syllables_per_sec": round(float(p["syllables_per_sec"]), 2),
            "pause_ratio_pct": round(float(p["pause_ratio"] * 100.0), 2),
            "rms_db": round(float(p["rms_db"]), 2),
            "pitch_mean_hz": round(float(p["pitch_mean_hz"]), 1),
            "pitch_std_hz": round(float(p["pitch_std_hz"]), 1),
            "duration_sec": round(float(p["duration"]), 2),
        })

    df_records = pd.DataFrame(records)
    clip_csv = out_dir / "test_behavior_telemetry.csv"
    df_records.to_csv(clip_csv, index=False)
    print(f"Saved clip-level telemetry to {clip_csv}")

    # Aggregate by emotion
    summary = df_records.groupby("emotion").agg(
        n=("filename", "count"),
        speed_mean=("syllables_per_sec", "mean"),
        speed_std=("syllables_per_sec", "std"),
        pause_mean=("pause_ratio_pct", "mean"),
        pause_std=("pause_ratio_pct", "std"),
        rms_mean=("rms_db", "mean"),
        rms_std=("rms_db", "std"),
        pitch_mean=("pitch_mean_hz", "mean"),
        pitch_std=("pitch_mean_hz", "std"),
        pitch_var_std=("pitch_std_hz", "mean"),
    ).reset_index()

    # Reorder emotions to match standard display order
    order = ["Angry", "Calm", "Happy", "Neutral", "Sad"]
    summary["emotion_cat"] = pd.Categorical(summary["emotion"], categories=order, ordered=True)
    summary = summary.sort_values("emotion_cat").drop(columns=["emotion_cat"])

    # Round columns
    summary["speed_mean"] = summary["speed_mean"].round(2)
    summary["speed_std"] = summary["speed_std"].round(2)
    summary["pause_mean"] = summary["pause_mean"].round(1)
    summary["pause_std"] = summary["pause_std"].round(1)
    summary["rms_mean"] = summary["rms_mean"].round(1)
    summary["rms_std"] = summary["rms_std"].round(1)
    summary["pitch_mean"] = summary["pitch_mean"].round(1)
    summary["pitch_std"] = summary["pitch_std"].round(1)
    summary["pitch_var_std"] = summary["pitch_var_std"].round(1)

    profile_csv = out_dir / "emotion_profiles.csv"
    summary.to_csv(profile_csv, index=False)
    print(f"Saved empirical emotion profiles to {profile_csv}:")
    print(summary.to_string())

if __name__ == "__main__":
    main()
