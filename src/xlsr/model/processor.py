"""
Hugging Face feature extractor for Wav2Vec2-XLS-R-300M.

Converts raw 16 kHz waveforms into model inputs (input_values, attention_mask).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Sequence, Union

import numpy as np
import torch
from transformers import BatchFeature

from xlsr.core.constants import MODEL_NAME, SAMPLE_RATE
from xlsr.data.audio import RawWaveform, load_raw_waveform
from xlsr.model.loader import load_hf_token, load_xlsr_feature_extractor

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
    token: str | None = None,
) -> ProcessorBundle:
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
    if sampling_rate != SAMPLE_RATE:
        raise ValueError(f"sampling_rate must be {SAMPLE_RATE}, got {sampling_rate}")

    if isinstance(waveforms, RawWaveform) or (
        isinstance(waveforms, np.ndarray) and waveforms.ndim == 1
    ):
        arrays = [_to_float_array(waveforms)]  # type: ignore[arg-type]
    elif isinstance(waveforms, (list, tuple)):
        if len(waveforms) == 0:
            raise ValueError("waveforms list is empty")
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

    return processor.feature_extractor(
        arrays,
        sampling_rate=SAMPLE_RATE,
        return_tensors=return_tensors,
        padding=padding,
        return_attention_mask=return_attention_mask,
    )


def encode_audio_file(
    processor: ProcessorBundle,
    path: Union[str, Path],
    **kwargs: Any,
) -> BatchFeature:
    raw = load_raw_waveform(path)
    return waveforms_to_model_inputs(processor, raw, **kwargs)


def summarize_model_inputs(encoded: BatchFeature) -> Dict[str, Any]:
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
