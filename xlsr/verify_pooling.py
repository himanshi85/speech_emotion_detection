#!/usr/bin/env python3
"""
Verify Section 8: masked mean pooling ignores padded frames.

Usage (from project root):
    python -m xlsr.verify_pooling
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.paths import DEFAULT_OUTPUT_DIR
from xlsr.pooling import run_pooling_verification


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify masked mean pooling")
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("verify_pooling")

    try:
        report = run_pooling_verification(
            output_dir=args.output_dir,
            stop_on_failure=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("%s", exc)
        return 1

    for check in report.checks:
        logger.info("%s", check)
    logger.info("Section 8 verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
