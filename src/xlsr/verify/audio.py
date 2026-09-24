"""Raw audio input verification runner."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from xlsr.core.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.data.audio import (
    AudioInputError,
    AudioVerificationReport,
    collect_split_audio_paths,
    load_raw_waveform,
    verify_audio_paths,
)
from xlsr.data.dataset import load_ravdess_splits
from xlsr.training.experiment import create_experiment_dirs

logger = logging.getLogger(__name__)


def run_audio_input_verification(
    data_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    *,
    max_per_split: Optional[int] = None,
    stop_on_failure: bool = True,
) -> AudioVerificationReport:
    data_root = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    out_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR

    exp = create_experiment_dirs(out_root)
    bundle = load_ravdess_splits(data_root)
    paths = collect_split_audio_paths(bundle, max_per_split=max_per_split)
    report = verify_audio_paths(paths)

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
