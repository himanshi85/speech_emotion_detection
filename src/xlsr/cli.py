"""
Unified CLI for XLS-R SER verification and (future) training.

Usage:
    python -m xlsr verify all
    python -m xlsr verify dataset
    python -m xlsr verify split
    ...
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Callable, List, Optional, Tuple

from xlsr.core.config import write_default_experiment_config
from xlsr.core.constants import MODEL_NAME, NUM_CHANNELS, SAMPLE_RATE
from xlsr.data.labels import (
    CLASS_NAMES,
    EMOTION_TO_ID,
    ID_TO_EMOTION,
    NUM_CLASSES,
    num_classifier_logits,
)
from xlsr.core.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.data.audio import AudioInputError
from xlsr.data.dataset import load_ravdess_splits, verify_actor_independent_split, write_dataset_summary
from xlsr.data.labels import LabelMappingError
from xlsr.data.split import ActorLeakageError
from xlsr.model.loader import load_hf_token, load_xlsr_from_hub
from xlsr.training.experiment import create_experiment_dirs
from xlsr.training.fine_tuning import add_freeze_encoder_argument, resolve_fine_tuning_mode
from xlsr.verify import (
    run_architecture_verification,
    run_audio_input_verification,
    run_fine_tuning_verification,
    run_head_verification,
    run_label_verification,
    run_pooling_verification,
    run_processor_verification,
    run_split_guard,
)

logger = logging.getLogger(__name__)

VerifyStep = Tuple[str, Callable[[argparse.Namespace], int]]


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def _common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data_dir", type=str, default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR))


def cmd_verify_model_load(args: argparse.Namespace) -> int:
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
    return 0


def cmd_verify_dataset(args: argparse.Namespace) -> int:
    exp_paths = create_experiment_dirs(args.output_dir)
    logger.info("Training results will be stored under: %s", exp_paths["root"])

    bundle = load_ravdess_splits(args.data_dir)
    ok, _ = verify_actor_independent_split(bundle, strict=True)
    logger.info("Actor-independent split OK: %s", ok)

    summary_path = write_dataset_summary(
        bundle,
        exp_paths["metrics"] / "dataset_summary.txt",
    )
    logger.info("Sizes: %s", bundle.sizes)
    logger.info("Summary: %s", summary_path)
    return 0


def cmd_verify_split(args: argparse.Namespace) -> int:
    run_split_guard(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        stop_on_failure=True,
    )
    return 0


def cmd_verify_labels(args: argparse.Namespace) -> int:
    logger.info("NUM_CLASSES=%d (model must output %d logits)", NUM_CLASSES, num_classifier_logits())
    logger.info("EMOTION_TO_ID=%s", EMOTION_TO_ID)
    logger.info("ID_TO_EMOTION=%s", ID_TO_EMOTION)
    logger.info("CLASS_NAMES=%s", CLASS_NAMES)
    run_label_verification(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        stop_on_failure=True,
    )
    return 0


def cmd_verify_audio(args: argparse.Namespace) -> int:
    logger.info(
        "Audio contract: raw waveform only | sr=%d | channels=%d | no MFCC/Mel",
        SAMPLE_RATE,
        NUM_CHANNELS,
    )
    run_audio_input_verification(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        max_per_split=args.max_per_split,
        stop_on_failure=True,
    )
    return 0


def cmd_verify_processor(args: argparse.Namespace) -> int:
    run_processor_verification(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        stop_on_failure=True,
    )
    return 0


def cmd_verify_architecture(args: argparse.Namespace) -> int:
    run_architecture_verification(
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        freeze_encoder=args.freeze_encoder,
        stop_on_failure=True,
    )
    return 0


def cmd_verify_pooling(args: argparse.Namespace) -> int:
    run_pooling_verification(output_dir=args.output_dir, stop_on_failure=True)
    return 0


def cmd_verify_head(args: argparse.Namespace) -> int:
    run_head_verification(output_dir=args.output_dir, stop_on_failure=True)
    return 0


def cmd_verify_fine_tuning(args: argparse.Namespace) -> int:
    plan = resolve_fine_tuning_mode(freeze_encoder=args.freeze_encoder)
    logger.info("CLI selection: %s", plan.description)

    cfg_path = write_default_experiment_config(
        output_dir=args.output_dir,
        freeze_encoder=args.freeze_encoder,
    )
    logger.info("Wrote experiment config: %s", cfg_path)

    result = run_fine_tuning_verification(
        output_dir=args.output_dir,
        stop_on_failure=True,
    )
    for check in result["checks"]:
        logger.info("%s", check)
    return 0


VERIFY_STEPS: List[VerifyStep] = [
    ("model_load", cmd_verify_model_load),
    ("dataset", cmd_verify_dataset),
    ("split", cmd_verify_split),
    ("labels", cmd_verify_labels),
    ("audio", cmd_verify_audio),
    ("processor", cmd_verify_processor),
    ("architecture", cmd_verify_architecture),
    ("pooling", cmd_verify_pooling),
    ("head", cmd_verify_head),
    ("fine_tuning", cmd_verify_fine_tuning),
]

LOCAL_ONLY_STEPS = {"pooling", "head", "fine_tuning"}


def cmd_verify_all(args: argparse.Namespace) -> int:
    for name, handler in VERIFY_STEPS:
        if args.skip_hub and name in {"model_load", "processor", "architecture"}:
            logger.info("Skipping %s (--skip_hub)", name)
            continue
        if args.skip_audio and name == "audio":
            logger.info("Skipping audio (--skip_audio)")
            continue
        logger.info("=== verify %s ===", name)
        try:
            rc = handler(args)
        except (ActorLeakageError, LabelMappingError, AudioInputError, RuntimeError) as exc:
            logger.error("verify %s FAILED: %s", name, exc)
            return 1
        if rc != 0:
            return rc
    logger.info("All verification steps passed.")
    return 0


def _add_verify_subparser(subparsers: argparse._SubParsersAction) -> None:
    verify = subparsers.add_parser("verify", help="Run verification checks")
    verify_sub = verify.add_subparsers(dest="verify_target", required=True)

    p_all = verify_sub.add_parser("all", help="Run all verification steps in order")
    _common_args(p_all)
    p_all.add_argument("--config_only", action="store_true")
    p_all.add_argument("--max_per_split", type=int, default=None)
    p_all.add_argument("--batch_size", type=int, default=2)
    add_freeze_encoder_argument(p_all)
    p_all.add_argument("--skip_hub", action="store_true", help="Skip HF Hub downloads")
    p_all.add_argument("--skip_audio", action="store_true", help="Skip full audio scan")
    p_all.set_defaults(handler=cmd_verify_all)

    step_builders = {
        "model_load": lambda p: p.add_argument("--config_only", action="store_true"),
        "dataset": lambda p: None,
        "split": lambda p: None,
        "labels": lambda p: None,
        "audio": lambda p: p.add_argument("--max_per_split", type=int, default=None),
        "processor": lambda p: None,
        "architecture": lambda p: (
            p.add_argument("--batch_size", type=int, default=2),
            add_freeze_encoder_argument(p),
        ),
        "pooling": lambda p: None,
        "head": lambda p: None,
        "fine_tuning": lambda p: add_freeze_encoder_argument(p),
    }

    handlers = dict(VERIFY_STEPS)
    for name, builder in step_builders.items():
        p = verify_sub.add_parser(name, help=f"Verify section: {name}")
        _common_args(p)
        builder(p)
        p.set_defaults(handler=handlers[name])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xlsr",
        description="Wav2Vec2-XLS-R-300M Speech Emotion Recognition",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_verify_subparser(subparsers)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    _setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return int(args.handler(args))
    except (ActorLeakageError, LabelMappingError, AudioInputError, RuntimeError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
