"""
Section 6 — Hugging Face feature extractor for Wav2Vec2-XLS-R-300M.

Uses:
    AutoFeatureExtractor.from_pretrained("facebook/wav2vec2-xls-r-300m")

Converts raw 16 kHz waveforms into model inputs:
    - input_values
    - attention_mask (when requested / padding is used)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import torch
from transformers import BatchFeature

from xlsr.audio_input import RawWaveform, load_raw_waveform
from xlsr.constants import MODEL_NAME, SAMPLE_RATE
from xlsr.model_loader import load_hf_token, load_xlsr_feature_extractor

logger = logging.getLogger(__name__)

WaveformLike = Union[np.ndarray, RawWaveform, Sequence[float]]


@dataclass(frozen=True)
class ProcessorBundle:
    """HF feature extractor locked to XLS-R-300M @ 16 kHz."""

    feature_extractor: Any
    model_name: str = MODEL_NAME
    sampling_rate: int = SAMPLE_RATE

    def __post_init__(self) -> None:
        sr = getattr(self.feature_extractor, "sampling_rate", None)
        if sr is not None and int(sr) != SAMPLE_RATE:
            raise ValueError(
                f"Feature extractor sampling_rate={sr}, expected {SAMPLE_RATE}"
            )


def get_xlsr_processor(
    model_name: str = MODEL_NAME,
    token: Optional[str] = None,
) -> ProcessorBundle:
    """
    Load the official HF AutoFeatureExtractor for facebook/wav2vec2-xls-r-300m.
    """
    if model_name != MODEL_NAME:
        raise ValueError(
            f"Processor must use exactly '{MODEL_NAME}'. Got: '{model_name}'"
        )
    if token is None:
        token = load_hf_token()

    extractor = load_xlsr_feature_extractor(model_name=model_name, token=token)
    sr = int(getattr(extractor, "sampling_rate", SAMPLE_RATE))
    logger.info(
        "HF processor ready | model=%s | sampling_rate=%d",
        model_name,
        sr,
    )
    return ProcessorBundle(
        feature_extractor=extractor,
        model_name=model_name,
        sampling_rate=sr,
    )


def _to_float_array(waveform: WaveformLike) -> np.ndarray:
    if isinstance(waveform, RawWaveform):
        arr = np.asarray(waveform.waveform, dtype=np.float32)
        if waveform.sample_rate != SAMPLE_RATE:
            raise ValueError(
                f"RawWaveform sample_rate={waveform.sample_rate}, expected {SAMPLE_RATE}"
            )
        return arr
    arr = np.asarray(waveform, dtype=np.float32)
    if arr.ndim != 1:
        raise ValueError(f"Expected 1-D waveform, got shape {arr.shape}")
    return arr


def waveforms_to_model_inputs(
    processor: ProcessorBundle,
    waveforms: Union[WaveformLike, Sequence[WaveformLike]],
    *,
    sampling_rate: int = SAMPLE_RATE,
    return_tensors: str = "pt",
    padding: Union[bool, str] = True,
    return_attention_mask: bool = True,
) -> BatchFeature:
    """
    Convert raw waveform(s) into Wav2Vec2 model inputs via the HF feature extractor.

    Returns a BatchFeature with at least:
      - input_values
      - attention_mask (if return_attention_mask=True)
    """
    if sampling_rate != SAMPLE_RATE:
        raise ValueError(f"sampling_rate must be {SAMPLE_RATE}, got {sampling_rate}")

    # Normalize to a list of 1-D float arrays
    if isinstance(waveforms, RawWaveform) or (
        isinstance(waveforms, np.ndarray) and waveforms.ndim == 1
    ):
        arrays = [_to_float_array(waveforms)]  # type: ignore[arg-type]
    elif isinstance(waveforms, (list, tuple)):
        if len(waveforms) == 0:
            raise ValueError("waveforms list is empty")
        # Single list of floats?
        if not isinstance(waveforms[0], (RawWaveform, np.ndarray, list, tuple)):
            arrays = [_to_float_array(np.asarray(waveforms, dtype=np.float32))]
        else:
            arrays = [_to_float_array(w) for w in waveforms]  # type: ignore[arg-type]
    else:
        arrays = [_to_float_array(waveforms)]  # type: ignore[arg-type]

    for i, arr in enumerate(arrays):
        if arr.size == 0:
            raise ValueError(f"waveform[{i}] is empty")
        if not np.isfinite(arr).all():
            raise ValueError(f"waveform[{i}] contains NaN/Inf")

    encoded = processor.feature_extractor(
        arrays,
        sampling_rate=SAMPLE_RATE,
        return_tensors=return_tensors,
        padding=padding,
        return_attention_mask=return_attention_mask,
    )
    return encoded


def encode_audio_file(
    processor: ProcessorBundle,
    path: Union[str, Path],
    **kwargs: Any,
) -> BatchFeature:
    """Load one preprocessed WAV as raw waveform, then encode with HF processor."""
    raw = load_raw_waveform(path)
    return waveforms_to_model_inputs(processor, raw, **kwargs)


def summarize_model_inputs(encoded: BatchFeature) -> Dict[str, Any]:
    """Small debug summary of processor outputs."""
    summary: Dict[str, Any] = {"keys": list(encoded.keys())}
    if "input_values" in encoded:
        iv = encoded["input_values"]
        summary["input_values_shape"] = tuple(iv.shape)
        summary["input_values_dtype"] = str(iv.dtype)
        if isinstance(iv, torch.Tensor):
            summary["input_values_device"] = str(iv.device)
    if "attention_mask" in encoded:
        am = encoded["attention_mask"]
        summary["attention_mask_shape"] = tuple(am.shape)
        summary["attention_mask_dtype"] = str(am.dtype)
    return summary


def run_processor_verification(
    data_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    *,
    num_samples: int = 4,
    stop_on_failure: bool = True,
) -> Dict[str, Any]:
    """
    Load HF processor and encode a few train waveforms.
    Writes a short report under outputs/.../metrics/.
    """
    from xlsr.dataset_io import load_ravdess_splits
    from xlsr.experiment_dirs import create_experiment_dirs
    from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR

    data_root = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    out_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    exp = create_experiment_dirs(out_root)

    issues: List[str] = []
    details: List[str] = []

    try:
        processor = get_xlsr_processor()
        details.append(f"model_name: {processor.model_name}")
        details.append(f"sampling_rate: {processor.sampling_rate}")
        details.append(
            f"feature_extractor_class: {processor.feature_extractor.__class__.__name__}"
        )
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Failed to load processor: {exc}")
        processor = None

    encoded_summary = None
    batch_summary = None
    if processor is not None:
        bundle = load_ravdess_splits(data_root)
        paths = [
            Path(p)
            for p in bundle.train["abs_filepath"].head(num_samples).tolist()
        ]
        try:
            # Single file
            single = encode_audio_file(processor, paths[0])
            encoded_summary = summarize_model_inputs(single)
            details.append(f"single_file: {paths[0].name}")
            details.append(f"single_inputs: {encoded_summary}")

            # Small batch (variable length → padding)
            raws = [load_raw_waveform(p) for p in paths]
            batch = waveforms_to_model_inputs(processor, raws, padding=True)
            batch_summary = summarize_model_inputs(batch)
            details.append(f"batch_size: {len(raws)}")
            details.append(f"batch_inputs: {batch_summary}")

            if "input_values" not in single:
                issues.append("Processor output missing input_values")
            if "attention_mask" not in single:
                issues.append("Processor output missing attention_mask")
        except Exception as exc:  # noqa: BLE001
            issues.append(f"Failed to encode waveforms: {exc}")

    ok = len(issues) == 0
    lines = [
        "Hugging Face Processor Verification (Section 6)",
        "=" * 60,
        f"Status: {'PASSED' if ok else 'FAILED'}",
        f"Model: {MODEL_NAME}",
        f"Required sampling_rate: {SAMPLE_RATE}",
        "",
        "API:",
        '  AutoFeatureExtractor.from_pretrained("facebook/wav2vec2-xls-r-300m")',
        "",
        "Details:",
    ]
    for d in details:
        lines.append(f"  {d}")
    if issues:
        lines.append("")
        lines.append("Issues:")
        for i in issues:
            lines.append(f"  - {i}")
    else:
        lines.append("")
        lines.append("Processor converts raw waveforms to input_values (+ attention_mask).")

    report_path = exp["metrics"] / "processor_verification.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Processor report written: %s", report_path)

    result = {
        "ok": ok,
        "issues": issues,
        "single": encoded_summary,
        "batch": batch_summary,
        "report_path": str(report_path),
    }
    if stop_on_failure and not ok:
        raise RuntimeError(
            "HF PROCESSOR VERIFICATION FAILED — stopping.\n"
            + "\n".join(f"  - {i}" for i in issues)
        )
    return result
