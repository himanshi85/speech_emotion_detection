#!/usr/bin/env python3
"""Train all 8 SER models sequentially."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import torch

from ser.core.config import load_model_config
from ser.core.paths import ALL_MODEL_KEYS
from ser.training.trainer import train_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("train_all")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train all SER models")
    parser.add_argument("--data_dir", type=str, default=None, help="Dataset directory (e.g. cremad_preprocessed)")
    parser.add_argument("--outputs_root", type=str, default=None, help="Outputs root directory (e.g. outputs/cremad)")
    parser.add_argument("--models", nargs="*", default=None, help="Subset of model keys to train")
    parser.add_argument("--skip", nargs="*", default=[], help="Model keys to skip")
    parser.add_argument("--epochs", type=int, default=None, help="Override number of epochs")
    parser.add_argument("--freeze_xlsr", action="store_true", default=True, help="Freeze encoder for wav2vec2_xlsr_300m")
    args = parser.parse_args()

    models_to_train = args.models if args.models else list(ALL_MODEL_KEYS)
    data_dir = Path(args.data_dir).resolve() if args.data_dir else None
    outputs_root = Path(args.outputs_root).resolve() if args.outputs_root else None

    failed = []
    completed = []

    for key in models_to_train:
        if key in args.skip:
            logger.info("Skipping %s", key)
            continue
        logger.info("========== Training %s ==========", key)
        try:
            overrides = {}
            if args.epochs is not None:
                overrides["num_epochs"] = args.epochs
            if data_dir is not None:
                overrides["data_dir"] = str(data_dir)
            if outputs_root is not None:
                overrides["output_dir"] = str(outputs_root / key)
            if key == "wav2vec2_xlsr_300m" and args.freeze_xlsr:
                overrides["freeze_encoder"] = True

            cfg = load_model_config(key, overrides=overrides)
            train_model(cfg)
            completed.append(key)

            # Keep leaderboard updated in real time
            try:
                from scripts.compare_results import main as compare_main
                sys_argv_backup = list(sys.argv)
                cmp_args = []
                if outputs_root:
                    cmp_args.extend(["--outputs_root", str(outputs_root), "--comparison_dir", str(outputs_root / "comparison")])
                sys.argv = ["compare_results.py"] + cmp_args
                compare_main()
                sys.argv = sys_argv_backup
            except Exception as cmp_err:
                logger.debug("Intermediate comparison update failed: %s", cmp_err)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed training %s: %s", key, exc)
            failed.append(key)
        finally:
            import gc
            gc.collect()
            if hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
                torch.mps.empty_cache()

    # Generate comparison if outputs_root is provided or completed models exist
    try:
        from scripts.compare_results import main as compare_main
        sys_argv_backup = list(sys.argv)
        cmp_args = []
        if outputs_root:
            cmp_args.extend(["--outputs_root", str(outputs_root), "--comparison_dir", str(outputs_root / "comparison")])
        sys.argv = ["compare_results.py"] + cmp_args
        logger.info("Generating leaderboard comparison...")
        compare_main()
        sys.argv = sys_argv_backup
    except Exception as cmp_exc:  # noqa: BLE001
        logger.warning("Could not auto-generate comparison: %s", cmp_exc)

    if failed:
        logger.error("Failed models: %s", failed)
        return 1

    logger.info("All requested models trained successfully: %s", completed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
