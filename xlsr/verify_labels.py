#!/usr/bin/env python3
"""
Verify Section 4: locked 8-class emotion mapping.

Usage (from project root):
    python -m xlsr.verify_labels
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.labels import (
    CLASS_NAMES,
    EMOTION_TO_ID,
    ID_TO_EMOTION,
    LabelMappingError,
    NUM_CLASSES,
    num_classifier_logits,
    run_label_verification,
)
from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify locked emotion label mapping")
    parser.add_argument("--data_dir", type=str, default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("verify_labels")

    logger.info("NUM_CLASSES=%d (model must output %d logits)", NUM_CLASSES, num_classifier_logits())
    logger.info("EMOTION_TO_ID=%s", EMOTION_TO_ID)
    logger.info("ID_TO_EMOTION=%s", ID_TO_EMOTION)
    logger.info("CLASS_NAMES=%s", CLASS_NAMES)

    try:
        report = run_label_verification(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            stop_on_failure=True,
        )
    except LabelMappingError as exc:
        logger.error("%s", exc)
        return 1

    logger.info("Section 4 verification OK | issues=%d", len(report.issues))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
