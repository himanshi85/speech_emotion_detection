"""
Section 5 — Raw audio input for Wav2Vec2-XLS-R-300M.

Loads preprocessed RAVDESS WAVs as raw waveforms only.

Contract:
  - mono
  - 16_000 Hz
  - WAV
  - no MFCC / Mel / pitch / energy / other handcrafted features
  - no extra model-specific transforms here (HF feature extractor is Section 6)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import soundfile as sf

from xlsr.constants import NUM_CHANNELS, SAMPLE_RATE

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]


class AudioInputError(RuntimeError):
    """Raised when audio cannot be loaded or fails the raw-input contract."""


@dataclass(frozen=True)
class RawWaveform:
    """Raw mono waveform ready for the HF feature extractor (later section)."""

    waveform: np.ndarray  # float32, shape (num_samples,)
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
    issues: List[str] = field(default_factory=list)
    sample_rate_expected: int = SAMPLE_RATE
    channels_expected: int = NUM_CHANNELS

    def to_text(self) -> str:
        status = "PASSED" if self.ok else "FAILED"
        lines = [
            "RAVDESS Raw Audio Input Verification (Section 5)",
            "=" * 60,
            f"Status: {status}",
            f"Expected: mono, {self.sample_rate_expected} Hz, raw waveform WAV",
            f"Checked files: {self.checked}",
            f"Failed files: {self.failed}",
            "",
            "Forbidden in this stage:",
            "  - MFCC",
            "  - Mel spectrogram",
            "  - handcrafted acoustic / pitch / energy features",
            "  - extra model-specific audio transforms",
            "",
            "Model input: raw waveform only.",
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
    """Return (mono_float32, num_channels_original). Does not remix stereo to 'fix'."""
    audio = np.asarray(audio)
    if audio.ndim == 1:
        return audio.astype(np.float32, copy=False), 1
    if audio.ndim == 2:
        # soundfile: (frames, channels)
        n_ch = int(audio.shape[1])
        if n_ch == 1:
            return audio[:, 0].astype(np.float32, copy=False), 1
        # Preprocessed data must already be mono; do not silently downmix.
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
    """
    Load a WAV file as a raw mono waveform.

    Verifies sampling_rate and channel count before returning.
    Does not extract MFCC/Mel or apply extra transforms.
    """
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
    """Return (ok, error_message)."""
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
    """Collect abs_filepath values from train/val/test (optionally capped per split)."""
    paths: List[Path] = []
    for df in (bundle.train, bundle.validation, bundle.test):
        col = "abs_filepath" if "abs_filepath" in df.columns else "filepath"
        series = df[col].tolist()
        if max_per_split is not None:
            series = series[: max_per_split]
        paths.extend(Path(p) for p in series)
    return paths


def run_audio_input_verification(
    data_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    *,
    max_per_split: Optional[int] = None,
    stop_on_failure: bool = True,
) -> AudioVerificationReport:
    """
    Verify raw audio contract on the existing preprocessed dataset.

    By default checks all files. Set max_per_split for a faster smoke test.
    """
    from xlsr.dataset_io import load_ravdess_splits
    from xlsr.experiment_dirs import create_experiment_dirs
    from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR

    data_root = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    out_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR

    exp = create_experiment_dirs(out_root)
    bundle = load_ravdess_splits(data_root)
    paths = collect_split_audio_paths(bundle, max_per_split=max_per_split)
    report = verify_audio_paths(paths)

    # Spot-check one successful load shape for the report log
    if paths:
        sample = load_raw_waveform(paths[0])
        logger.info(
            "Sample raw waveform: path=%s sr=%d ch=%d samples=%d duration=%.4fs dtype=%s",
            sample.path.name,
            sample.sample_rate,
            sample.num_channels,
            sample.num_samples,
            sample.duration,
            sample.waveform.dtype,
        )

    report_path = exp["metrics"] / "audio_input_verification.txt"
    report_path.write_text(report.to_text(), encoding="utf-8")
    logger.info("Audio input report written: %s", report_path)

    if stop_on_failure and not report.ok:
        raise AudioInputError(
            "RAW AUDIO INPUT VERIFICATION FAILED — stopping.\n"
            + "\n".join(f"  - {i}" for i in report.issues[:20])
            + f"\nSee report: {report_path}"
        )
    return report
