"""
Raw audio waveform loader and validator for Speech Emotion Recognition (SER).

Loads preprocessed audio as 16 kHz mono raw waveforms.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
import soundfile as sf

from ser.core.constants import NUM_CHANNELS, SAMPLE_RATE

PathLike = Union[str, Path]


class AudioInputError(RuntimeError):
    """Raised when audio cannot be loaded or fails the raw-input contract."""


@dataclass(frozen=True)
class RawWaveform:
    """Raw mono waveform ready for model ingestion."""

    waveform: np.ndarray
    sample_rate: int
    num_channels: int
    path: Path
    duration: float

    @property
    def num_samples(self) -> int:
        return int(self.waveform.shape[0])


@dataclass
class AudioVerificationReport:
    ok: bool
    checked: int
    failed: int
    issues: List[str]
    sample_rate_expected: int = SAMPLE_RATE
    channels_expected: int = NUM_CHANNELS

    def to_text(self) -> str:
        status = "PASSED" if self.ok else "FAILED"
        lines = [
            "Raw Audio Input Verification",
            "=" * 60,
            f"Status: {status}",
            f"Expected: mono, {self.sample_rate_expected} Hz, raw waveform WAV",
            f"Checked files: {self.checked}",
            f"Failed files: {self.failed}",
        ]
        if self.issues:
            lines.append("")
            lines.append("Issues:")
            for issue in self.issues[:50]:
                lines.append(f"  - {issue}")
            if len(self.issues) > 50:
                lines.append(f"  ... and {len(self.issues) - 50} more")
        else:
            lines.append("")
            lines.append("All checked files are valid raw mono 16 kHz waveforms.")
        return "\n".join(lines) + "\n"


def _as_mono(audio: np.ndarray) -> Tuple[np.ndarray, int]:
    audio = np.asarray(audio)
    if audio.ndim == 1:
        return audio.astype(np.float32, copy=False), 1
    if audio.ndim == 2:
        n_ch = int(audio.shape[1])
        if n_ch == 1:
            return audio[:, 0].astype(np.float32, copy=False), 1
        raise AudioInputError(
            f"Expected mono audio (1 channel), got {n_ch} channels"
        )
    raise AudioInputError(f"Unexpected audio ndim={audio.ndim}")


def load_raw_waveform(
    path: PathLike,
    *,
    expected_sr: int = SAMPLE_RATE,
    expected_channels: int = NUM_CHANNELS,
) -> RawWaveform:
    """Load a WAV file as a raw mono waveform."""
    path = Path(path)
    if not path.exists():
        raise AudioInputError(f"Audio file does not exist: {path}")

    try:
        audio, sr = sf.read(str(path), always_2d=False, dtype="float32")
    except Exception as exc:  # noqa: BLE001
        raise AudioInputError(f"Failed to load audio {path}: {exc}") from exc

    sr = int(sr)
    if sr != expected_sr:
        raise AudioInputError(
            f"{path.name}: sampling_rate={sr}, expected {expected_sr}"
        )

    waveform, n_ch = _as_mono(np.asarray(audio))
    if n_ch != expected_channels:
        raise AudioInputError(
            f"{path.name}: channels={n_ch}, expected {expected_channels}"
        )

    if waveform.size == 0:
        raise AudioInputError(f"{path.name}: empty waveform")

    if not np.isfinite(waveform).all():
        raise AudioInputError(f"{path.name}: NaN/Inf values in waveform")

    duration = float(waveform.shape[0] / sr)
    if duration <= 0:
        raise AudioInputError(f"{path.name}: duration <= 0")

    return RawWaveform(
        waveform=waveform,
        sample_rate=sr,
        num_channels=n_ch,
        path=path.resolve(),
        duration=duration,
    )


def validate_raw_waveform(
    path: PathLike,
    *,
    expected_sr: int = SAMPLE_RATE,
    expected_channels: int = NUM_CHANNELS,
) -> Tuple[bool, Optional[str]]:
    try:
        load_raw_waveform(
            path,
            expected_sr=expected_sr,
            expected_channels=expected_channels,
        )
        return True, None
    except AudioInputError as exc:
        return False, str(exc)


def verify_audio_paths(
    paths: Sequence[PathLike],
    *,
    expected_sr: int = SAMPLE_RATE,
    expected_channels: int = NUM_CHANNELS,
) -> AudioVerificationReport:
    issues: List[str] = []
    failed = 0
    for path in paths:
        ok, err = validate_raw_waveform(
            path,
            expected_sr=expected_sr,
            expected_channels=expected_channels,
        )
        if not ok:
            failed += 1
            issues.append(err or f"Unknown failure for {path}")

    return AudioVerificationReport(
        ok=failed == 0,
        checked=len(paths),
        failed=failed,
        issues=issues,
        sample_rate_expected=expected_sr,
        channels_expected=expected_channels,
    )


def collect_split_audio_paths(bundle, max_per_split: Optional[int] = None) -> List[Path]:
    """Collect abs_filepath values from train/val/test."""
    paths: List[Path] = []
    for df in (bundle.train, bundle.validation, bundle.test):
        col = "abs_filepath" if "abs_filepath" in df.columns else "filepath"
        series = df[col].tolist()
        if max_per_split is not None:
            series = series[:max_per_split]
        paths.extend(Path(p) for p in series)
    return paths
