#!/usr/bin/env python3
"""
Verify Section 7: Wav2Vec2-XLS-R-300M SER architecture (8 logits).

Usage (from project root):
    python -m xlsr.verify_architecture
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.verify import run_architecture_verification
from xlsr.paths import DEFAULT_OUTPUT_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify XLS-R SER architecture")
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument(
        "--freeze_encoder",
        action="store_true",
        help="Optional: build with frozen encoder (Section 10 Mode A preview)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("verify_architecture")

    try:
        result = run_architecture_verification(
            output_dir=args.output_dir,
            batch_size=args.batch_size,
            freeze_encoder=args.freeze_encoder,
            stop_on_failure=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("%s", exc)
        return 1

    logger.info("logits_shape=%s", result.logits_shape)
    logger.info("params=%s", result.param_counts)
    logger.info("Section 7 verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
