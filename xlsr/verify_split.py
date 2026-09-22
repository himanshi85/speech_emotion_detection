#!/usr/bin/env python3
"""
Verify Section 3: actor-independent split guard.

Stops with a non-zero exit code if leakage is detected.

Usage (from project root):
    python -m xlsr.verify_split
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.split_guard import ActorLeakageError, run_split_guard


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify actor-independent dataset split")
    parser.add_argument("--data_dir", type=str, default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("verify_split")

    try:
        report = run_split_guard(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            stop_on_failure=True,
        )
    except ActorLeakageError as exc:
        logger.error("%s", exc)
        logger.error("Section 3 FAILED — do not start training")
        return 1

    logger.info("Train ∩ Validation = %s", report.intersections["train_validation"])
    logger.info("Train ∩ Test       = %s", report.intersections["train_test"])
    logger.info("Validation ∩ Test  = %s", report.intersections["validation_test"])
    logger.info("Section 3 verification OK — safe to proceed to training later")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
