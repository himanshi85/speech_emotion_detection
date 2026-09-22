#!/usr/bin/env python3
"""
Verify Section 6: Hugging Face AutoFeatureExtractor for XLS-R-300M.

Usage (from project root):
    python -m xlsr.verify_processor
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.constants import MODEL_NAME, SAMPLE_RATE
from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.processor import get_xlsr_processor, run_processor_verification


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify HF XLS-R feature extractor")
    parser.add_argument("--data_dir", type=str, default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--num_samples", type=int, default=4)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("verify_processor")

    logger.info("Loading AutoFeatureExtractor for %s @ %d Hz", MODEL_NAME, SAMPLE_RATE)
    processor = get_xlsr_processor()
    logger.info(
        "Loaded %s | sampling_rate=%s",
        processor.feature_extractor.__class__.__name__,
        processor.sampling_rate,
    )

    try:
        result = run_processor_verification(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            num_samples=args.num_samples,
            stop_on_failure=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("%s", exc)
        return 1

    logger.info("Single encode: %s", result.get("single"))
    logger.info("Batch encode: %s", result.get("batch"))
    logger.info("Section 6 verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
