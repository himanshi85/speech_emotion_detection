#!/usr/bin/env python3
"""Verify all 8 SER models: build, parameter counts, forward pass."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import torch

from ser.core.config import load_model_config
from ser.core.paths import ALL_MODEL_KEYS, OUTPUTS_ROOT
from ser.core.registry import HUB_IDS, build_model


def main() -> int:
    lines = []
    issues = []
    lines.append("SER Model Parameter Verification Report")
    lines.append("=" * 72)
    header = f"{'Model':<22} {'Hub / Arch':<36} {'Total':>12} {'Train':>10} {'Enc':>12} {'Head':>8} {'H':>5} {'Out':<10}"
    lines.append(header)
    lines.append("-" * len(header))

    for key in ALL_MODEL_KEYS:
        cfg = load_model_config(key)
        meta = HUB_IDS.get(key, {})
        hub_id = cfg.get("hub_id") or meta.get("hub_id", meta.get("architecture", "N/A"))

        try:
            model = build_model(cfg)
            counts = model.count_parameters()
            input_type = cfg.get("input_type") or meta.get("input_type", "waveform")

            if input_type == "mfcc":
                batch = {
                    "mfcc": torch.randn(2, 40, 100),
                    "attention_mask": torch.ones(2, 100, dtype=torch.long),
                }
            else:
                batch = {
                    "input_values": torch.randn(2, 16000),
                    "attention_mask": torch.ones(2, 16000, dtype=torch.long),
                }

            with torch.no_grad():
                out = model(**batch)
            logits_shape = tuple(out["logits"].shape)
            status = "OK" if logits_shape == (2, 8) else f"BAD {logits_shape}"

            if logits_shape != (2, 8):
                issues.append(f"{key}: logits {logits_shape} != (2, 8)")

            # Flag proxy backends
            if key == "emotion2vec_plus" and "wav2vec2-base" in str(hub_id):
                issues.append(
                    f"{key}: using Wav2Vec2-base proxy (~94M); true emotion2vec+ is ~90M via FunASR"
                )
            if key == "beats" and "wavlm" in str(hub_id).lower():
                issues.append(
                    f"{key}: using WavLM proxy; official BEATs is separate Microsoft checkpoint"
                )

            hidden = counts.get("hidden_size", "-")
            lines.append(
                f"{key:<22} {str(hub_id):<36} {counts['total']:>12,} "
                f"{counts['trainable']:>10,} {counts.get('encoder', 0):>12,} "
                f"{counts.get('head', 0):>8,} {str(hidden):>5} {status:<10}"
            )

            lines.append(f"  arch: {meta.get('architecture', '-')}")
            lines.append(f"  expected: {meta.get('expected_params', '-')}")
            lines.append("")

            del model
        except Exception as exc:  # noqa: BLE001
            lines.append(f"{key:<22} {str(hub_id):<36} {'FAIL':>12}")
            lines.append(f"  error: {exc}")
            lines.append("")
            issues.append(f"{key}: {exc}")

    lines.append("Training hyperparameters (from config):")
    lines.append("-" * 72)
    for key in ALL_MODEL_KEYS:
        cfg = load_model_config(key)
        lr = cfg.get("learning_rate") or (
            f"enc={cfg.get('encoder_learning_rate')} head={cfg.get('classifier_learning_rate')}"
        )
        lines.append(
            f"  {key:<22} epochs={cfg.get('num_epochs', '?'):>3} "
            f"batch={cfg.get('batch_size', '?'):>3} "
            f"accum={cfg.get('gradient_accumulation_steps', 1):>2} "
            f"lr={lr} dropout={cfg.get('dropout')} cw={cfg.get('class_weights', True)}"
        )

    lines.append("")
    lines.append("Expected parameter summary:")
    lines.append("  mfcc_lstm          ~833K   (LSTM encoder + 2K head)")
    lines.append("  mfcc_cnn_bilstm    ~925K   (CNN+BiLSTM + 2K head)")
    lines.append("  wav2vec2           ~94M    (768 hidden, 6K head)")
    lines.append("  hubert             ~94M    (768 hidden, 6K head)")
    lines.append("  wavlm              ~94M    (768 hidden, 6K head)")
    lines.append("  wav2vec2_xlsr_300m ~315M   (1024 hidden, 8K head)")
    lines.append("  emotion2vec_plus   ~90M    (true; currently wav2vec2 proxy)")
    lines.append("  beats              ~90M    (true BEATs; currently wavlm proxy)")

    if issues:
        lines.append("")
        lines.append("Notes / warnings:")
        for i in issues:
            lines.append(f"  - {i}")
    else:
        lines.append("")
        lines.append("All models built with correct 8-logit output.")

    report = "\n".join(lines) + "\n"
    print(report)

    out_path = OUTPUTS_ROOT / "comparison" / "model_parameter_report.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
