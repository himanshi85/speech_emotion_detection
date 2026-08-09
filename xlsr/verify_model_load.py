#!/usr/bin/env python3
"""
Verify Section 1: load facebook/wav2vec2-xls-r-300m from the Hugging Face Hub.

Usage (from project root):
    python -m xlsr.verify_model_load
    python -m xlsr.verify_model_load --config_only
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow running as script or module from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.constants import MODEL_NAME
from xlsr.model_loader import load_hf_token, load_xlsr_from_hub


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify XLS-R-300M Hub load")
    parser.add_argument(
        "--config_only",
        action="store_true",
        help="Load config + feature extractor only (skip downloading full weights)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("verify_model_load")

    token = load_hf_token()
    logger.info("Model ID (locked): %s", MODEL_NAME)
    logger.info("HF token present: %s", bool(token))

    model, feature_extractor, config = load_xlsr_from_hub(
        model_name=MODEL_NAME,
        token=token,
        load_weights=not args.config_only,
    )

    logger.info("Config hidden_size=%s", config.hidden_size)
    logger.info(
        "Feature extractor sampling_rate=%s",
        getattr(feature_extractor, "sampling_rate", None),
    )
    if model is not None:
        n_params = sum(p.numel() for p in model.parameters())
        logger.info("Encoder loaded successfully | parameters=%s", f"{n_params:,}")
    else:
        logger.info("Skipped weight download (--config_only)")

    logger.info("Section 1 verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
