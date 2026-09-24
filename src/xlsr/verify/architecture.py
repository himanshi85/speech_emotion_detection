"""SER architecture verification runner."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import torch

from xlsr.core.constants import MODEL_NAME
from xlsr.core.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.data.audio import load_raw_waveform
from xlsr.data.dataset import load_ravdess_splits
from xlsr.data.labels import NUM_CLASSES
from xlsr.model.processor import get_xlsr_processor, waveforms_to_model_inputs
from xlsr.model.ser import DEFAULT_DROPOUT, build_xlsr_ser_model
from xlsr.training.experiment import create_experiment_dirs

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureVerificationResult:
    ok: bool
    logits_shape: Tuple[int, ...]
    param_counts: dict
    issues: list


def run_architecture_verification(
    output_dir: Optional[str] = None,
    *,
    batch_size: int = 2,
    freeze_encoder: bool = False,
    stop_on_failure: bool = True,
) -> ArchitectureVerificationResult:
    out_root = output_dir or str(DEFAULT_OUTPUT_DIR)
    exp = create_experiment_dirs(out_root)
    issues = []

    model = build_xlsr_ser_model(freeze_encoder=freeze_encoder)
    model.eval()
    counts = model.count_parameters()

    processor = get_xlsr_processor()
    bundle = load_ravdess_splits(DEFAULT_DATA_DIR)
    paths = bundle.train["abs_filepath"].head(batch_size).tolist()
    raws = [load_raw_waveform(p) for p in paths]
    encoded = waveforms_to_model_inputs(processor, raws, padding=True)

    with torch.no_grad():
        out = model(
            input_values=encoded["input_values"],
            attention_mask=encoded.get("attention_mask"),
        )

    logits = out.logits
    logits_shape = tuple(logits.shape)
    expected = (batch_size, NUM_CLASSES)
    if logits_shape != expected:
        issues.append(f"logits shape {logits_shape} != expected {expected}")
    if logits_shape[-1] != NUM_CLASSES:
        issues.append(f"Model must output {NUM_CLASSES} logits, got {logits_shape[-1]}")

    if hasattr(model, "lm_head"):
        issues.append("Unexpected ASR/CTC lm_head found on SER model")

    ok = len(issues) == 0
    lines = [
        "Wav2Vec2-XLS-R-300M SER Architecture Verification (Section 7)",
        "=" * 60,
        f"Status: {'PASSED' if ok else 'FAILED'}",
        f"Encoder: Wav2Vec2Model ({MODEL_NAME})",
        "Head: Dropout -> Linear(hidden_size -> 8)  [no CTC/ASR]",
        "Pooling: masked mean over temporal dimension",
        "",
        f"hidden_size: {counts['hidden_size']}",
        f"num_classes (logits): {counts['num_classes']}",
        f"dropout: {DEFAULT_DROPOUT}",
        f"freeze_encoder: {freeze_encoder}",
        f"logits_shape: {logits_shape}",
        "",
        "Parameters:",
        f"  total:     {counts['total']:,}",
        f"  trainable: {counts['trainable']:,}",
        f"  encoder:   {counts['encoder']:,}",
        f"  classifier:{counts['classifier']:,}",
        "",
        "Forward path:",
        "  input_values -> Wav2Vec2Model -> last_hidden_state",
        "  -> masked_mean_pooling -> dropout -> linear -> 8 logits",
    ]
    if issues:
        lines.append("")
        lines.append("Issues:")
        for i in issues:
            lines.append(f"  - {i}")

    report_path = exp["metrics"] / "architecture_verification.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Architecture report written: %s", report_path)

    result = ArchitectureVerificationResult(
        ok=ok,
        logits_shape=logits_shape,
        param_counts=counts,
        issues=issues,
    )
    if stop_on_failure and not ok:
        raise RuntimeError(
            "ARCHITECTURE VERIFICATION FAILED\n"
            + "\n".join(f"  - {i}" for i in issues)
        )
    return result
