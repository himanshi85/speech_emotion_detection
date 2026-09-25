#!/usr/bin/env python3
"""
Audio Behaviour Analysis CLI Entrypoint
=======================================
Generates a complete Audio Behaviour Analysis Report for any input audio recording:
1. Emotion & Model Confidence (via trained SER Foundation Model).
2. Speaking Speed (syllables/sec and descriptive tempo).
3. Pause Frequency (pauses/min and silence duration ratio).
4. Vocal Energy (RMS dB loudness).
5. Pitch Variation (F0 stability and intonation).
6. Overall Speaker Behaviour Profile (Engaged, Hesitant, Monotone, Agitated, etc.).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import torch

from ser.core.config import load_model_config
from ser.features.behavior import analyze_audio_file
from ser.training.trainer import load_checkpoint_model

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Audio Behaviour Analysis Report")
    parser.add_argument("--audio", type=str, required=True, help="Path to input audio WAV file")
    parser.add_argument(
        "--model_ckpt",
        type=str,
        default=None,
        help="Path to trained model checkpoint (defaults to Universal HuBERT)",
    )
    parser.add_argument("--model_key", type=str, default="hubert", help="Model key (default: hubert)")
    parser.add_argument("--json", action="store_true", help="Output result as JSON instead of text report")
    args = parser.parse_args()

    audio_path = Path(args.audio).resolve()
    if not audio_path.exists():
        print(f"Error: Audio file not found at: {audio_path}", file=sys.stderr)
        return 1

    # Default checkpoint: Universal HuBERT or CREMA-D HuBERT
    if args.model_ckpt:
        ckpt_path = Path(args.model_ckpt).resolve()
    else:
        universal_ckpt = PROJECT_ROOT / "outputs" / "combined" / "universal_hubert_weighted_frozen" / "checkpoints" / "best_model" / "model.pt"
        cremad_ckpt = PROJECT_ROOT / "outputs" / "cremad" / "hubert" / "checkpoints" / "best_model" / "model.pt"
        if universal_ckpt.exists():
            ckpt_path = universal_ckpt
        elif cremad_ckpt.exists():
            ckpt_path = cremad_ckpt
        else:
            ckpt_path = None

    device = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))

    model = None
    cfg = None
    label_map = None

    if ckpt_path and ckpt_path.exists():
        try:
            # Look for labels.json
            for search_dir in [ckpt_path.parent, ckpt_path.parent.parent, ckpt_path.parent.parent.parent]:
                lm_file = search_dir / "labels.json"
                if lm_file.exists():
                    with open(lm_file) as f:
                        label_map = json.load(f)
                    break

            cfg = load_model_config(args.model_key)
            if label_map:
                cfg["num_classes"] = len(label_map)
                cfg["classes"] = label_map
            cfg["layer_pooling"] = "weighted"
            model = load_checkpoint_model(ckpt_path, cfg, device)
        except Exception as e:
            # Fallback if checkpoint cannot be loaded
            model = None

    metrics = analyze_audio_file(
        audio_path=audio_path,
        model=model,
        cfg=cfg,
        device=device,
        label_mapping=label_map,
    )

    if args.json:
        data = {
            "file": str(audio_path),
            "duration": metrics.audio_duration_seconds,
            "emotion": metrics.emotion,
            "confidence": round(metrics.confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in metrics.probabilities.items()},
            "speaking_speed": {
                "category": metrics.speaking_speed,
                "syllables_per_second": round(metrics.syllables_per_second, 2),
                "words_per_minute": round(metrics.words_per_minute, 1),
            },
            "pause_frequency": {
                "category": metrics.pause_frequency,
                "pauses_per_minute": round(metrics.pauses_per_minute, 1),
                "silence_ratio": round(metrics.pause_ratio, 3),
            },
            "energy": {
                "category": metrics.energy,
                "rms_db": round(metrics.rms_db, 1),
            },
            "pitch_variation": {
                "category": metrics.pitch_variation,
                "mean_hz": round(metrics.pitch_mean_hz, 1),
                "std_hz": round(metrics.pitch_std_hz, 1),
            },
            "overall_behaviour": metrics.overall_behaviour,
        }
        print(json.dumps(data, indent=2))
    else:
        print(metrics.to_report())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
