"""
Fine-tuning strategy for Wav2Vec2-XLS-R-300M SER.

Mode A — Frozen encoder: train classification head only (--freeze_encoder)
Mode B — Full fine-tuning: train encoder + head (DEFAULT)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple

import torch.nn as nn

from xlsr.model.ser import Wav2Vec2XLSRForSER, build_xlsr_ser_model

logger = logging.getLogger(__name__)


class FineTuningMode(str, Enum):
    FROZEN_ENCODER = "frozen_encoder"
    FULL = "full"


DEFAULT_FINE_TUNING_MODE = FineTuningMode.FULL


@dataclass(frozen=True)
class FineTuningPlan:
    mode: FineTuningMode
    freeze_encoder: bool

    @property
    def description(self) -> str:
        if self.mode == FineTuningMode.FROZEN_ENCODER:
            return "Mode A — Frozen encoder (train classification head only)"
        return "Mode B — Full fine-tuning (encoder + classification head)"


def resolve_fine_tuning_mode(freeze_encoder: bool = False) -> FineTuningPlan:
    if freeze_encoder:
        return FineTuningPlan(mode=FineTuningMode.FROZEN_ENCODER, freeze_encoder=True)
    return FineTuningPlan(mode=FineTuningMode.FULL, freeze_encoder=False)


def apply_fine_tuning_strategy(
    model: Wav2Vec2XLSRForSER,
    freeze_encoder: bool = False,
) -> FineTuningPlan:
    plan = resolve_fine_tuning_mode(freeze_encoder=freeze_encoder)
    if plan.freeze_encoder:
        model.freeze_encoder_parameters()
    else:
        model.unfreeze_encoder_parameters()
    logger.info("Applied fine-tuning strategy: %s", plan.description)
    return plan


def build_model_for_strategy(
    freeze_encoder: bool = False,
    **kwargs,
) -> Tuple[Wav2Vec2XLSRForSER, FineTuningPlan]:
    plan = resolve_fine_tuning_mode(freeze_encoder=freeze_encoder)
    model = build_xlsr_ser_model(freeze_encoder=plan.freeze_encoder, **kwargs)
    return model, plan


def trainable_parameter_summary(model: nn.Module) -> Dict[str, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    frozen = total - trainable

    encoder_total = 0
    encoder_trainable = 0
    head_trainable = 0
    if hasattr(model, "encoder"):
        encoder_total = sum(p.numel() for p in model.encoder.parameters())
        encoder_trainable = sum(
            p.numel() for p in model.encoder.parameters() if p.requires_grad
        )
    if hasattr(model, "classifier"):
        head_trainable += sum(
            p.numel() for p in model.classifier.parameters() if p.requires_grad
        )
    if hasattr(model, "dropout"):
        head_trainable += sum(
            p.numel() for p in model.dropout.parameters() if p.requires_grad
        )

    return {
        "total": total,
        "trainable": trainable,
        "frozen": frozen,
        "encoder_total": encoder_total,
        "encoder_trainable": encoder_trainable,
        "head_trainable": head_trainable,
    }


def encoder_requires_grad(model: Wav2Vec2XLSRForSER) -> bool:
    flags = [p.requires_grad for p in model.encoder.parameters()]
    if not flags:
        return False
    return any(flags)


def classifier_requires_grad(model: Wav2Vec2XLSRForSER) -> bool:
    return all(p.requires_grad for p in model.classifier.parameters())


def add_freeze_encoder_argument(parser) -> None:
    parser.add_argument(
        "--freeze_encoder",
        action="store_true",
        help=(
            "Mode A: freeze XLS-R encoder and train classification head only. "
            "Without this flag, Mode B full fine-tuning is used (default)."
        ),
    )
