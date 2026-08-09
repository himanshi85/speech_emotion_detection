#!/usr/bin/env python3
"""
Verify Section 5: raw mono 16 kHz waveform input (no handcrafted features).

Usage (from project root):
    python -m xlsr.verify_audio_input
    python -m xlsr.verify_audio_input --max_per_split 20
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.audio_input import AudioInputError, run_audio_input_verification
from xlsr.constants import NUM_CHANNELS, SAMPLE_RATE
from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify raw audio input contract")
    parser.add_argument("--data_dir", type=str, default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--max_per_split",
        type=int,
        default=None,
        help="Optional cap per split for a faster smoke test",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("verify_audio_input")

    logger.info(
        "Audio contract: raw waveform only | sr=%d | channels=%d | no MFCC/Mel",
        SAMPLE_RATE,
        NUM_CHANNELS,
    )

    try:
        report = run_audio_input_verification(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            max_per_split=args.max_per_split,
            stop_on_failure=True,
        )
    except AudioInputError as exc:
        logger.error("%s", exc)
        return 1

    logger.info(
        "Section 5 verification OK | checked=%d failed=%d",
        report.checked,
        report.failed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
