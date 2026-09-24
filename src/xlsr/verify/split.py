"""Actor-independent split verification runner."""

from __future__ import annotations

import logging
from pathlib import Path

from xlsr.core.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.data.dataset import load_ravdess_splits
from xlsr.data.split import ActorLeakageError, SplitVerificationReport, verify_dataset_split
from xlsr.training.experiment import create_experiment_dirs

logger = logging.getLogger(__name__)


def run_split_guard(
    data_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    stop_on_failure: bool = True,
) -> SplitVerificationReport:
    data_root = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    out_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR

    exp = create_experiment_dirs(out_root)
    bundle = load_ravdess_splits(data_root)
    report = verify_dataset_split(bundle)

    report_path = exp["metrics"] / "split_verification.txt"
    report_path.write_text(report.to_text(), encoding="utf-8")
    logger.info("Split verification report written: %s", report_path)

    if stop_on_failure and not report.ok:
        raise ActorLeakageError(
            "ACTOR LEAKAGE / SPLIT FAILURE — stopping execution.\n"
            + "\n".join(f"  - {i}" for i in report.issues)
            + f"\nSee report: {report_path}"
        )

    return report
