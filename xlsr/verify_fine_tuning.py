#!/usr/bin/env python3
"""
Verify Section 10: fine-tuning modes (frozen encoder vs full FT).

Usage (from project root):
    python -m xlsr.verify_fine_tuning
    python -m xlsr.verify_fine_tuning --freeze_encoder   # only affects written config demo
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.config import write_default_experiment_config
from xlsr.fine_tuning import (
    add_freeze_encoder_argument,
    resolve_fine_tuning_mode,
    run_fine_tuning_verification,
)
from xlsr.paths import DEFAULT_OUTPUT_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify fine-tuning strategy modes")
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    add_freeze_encoder_argument(parser)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("verify_fine_tuning")

    plan = resolve_fine_tuning_mode(freeze_encoder=args.freeze_encoder)
    logger.info("CLI selection: %s", plan.description)

    # Persist config reflecting CLI choice into experiment output folder
    cfg_path = write_default_experiment_config(
        output_dir=args.output_dir,
        freeze_encoder=args.freeze_encoder,
    )
    logger.info("Wrote experiment config: %s", cfg_path)

    try:
        result = run_fine_tuning_verification(
            output_dir=args.output_dir,
            stop_on_failure=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("%s", exc)
        return 1

    for check in result["checks"]:
        logger.info("%s", check)
    logger.info("Section 10 verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
