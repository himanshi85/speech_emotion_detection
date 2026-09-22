"""
Section 10 — Fine-tuning strategy for Wav2Vec2-XLS-R-300M SER.

Mode A — Frozen encoder: train classification head only (--freeze_encoder)
Mode B — Full fine-tuning: train encoder + head (DEFAULT)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import torch.nn as nn

from xlsr.model import Wav2Vec2XLSRForSER, build_xlsr_ser_model

logger = logging.getLogger(__name__)


class FineTuningMode(str, Enum):
    FROZEN_ENCODER = "frozen_encoder"  # Mode A
    FULL = "full"  # Mode B (default)


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
    """
    CLI / config rule:
      --freeze_encoder  -> Mode A
      otherwise         -> Mode B (full fine-tuning, default)
    """
    if freeze_encoder:
        return FineTuningPlan(mode=FineTuningMode.FROZEN_ENCODER, freeze_encoder=True)
    return FineTuningPlan(mode=FineTuningMode.FULL, freeze_encoder=False)


def apply_fine_tuning_strategy(
    model: Wav2Vec2XLSRForSER,
    freeze_encoder: bool = False,
) -> FineTuningPlan:
    """Apply Mode A or Mode B to an existing model instance."""
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
    """Build SER model with the selected fine-tuning mode (default = full FT)."""
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
    """Attach the Section 10 CLI flag to an argparse parser."""
    parser.add_argument(
        "--freeze_encoder",
        action="store_true",
        help=(
            "Mode A: freeze XLS-R encoder and train classification head only. "
            "Without this flag, Mode B full fine-tuning is used (default)."
        ),
    )


def verify_fine_tuning_modes() -> Tuple[bool, List[str], List[str], dict]:
    """
    Build Mode A and Mode B models and verify trainable parameter contracts.
    """
    issues: List[str] = []
    checks: List[str] = []
    details: dict = {}

    # Default resolution without flag
    default_plan = resolve_fine_tuning_mode(freeze_encoder=False)
    if default_plan.mode != FineTuningMode.FULL:
        issues.append("Default mode must be full fine-tuning (Mode B)")
        checks.append("FAIL: default is Mode B")
    else:
        checks.append("PASS: default (no --freeze_encoder) is Mode B full fine-tuning")

    frozen_plan = resolve_fine_tuning_mode(freeze_encoder=True)
    if frozen_plan.mode != FineTuningMode.FROZEN_ENCODER:
        issues.append("--freeze_encoder must select Mode A")
        checks.append("FAIL: --freeze_encoder selects Mode A")
    else:
        checks.append("PASS: --freeze_encoder selects Mode A frozen encoder")

    # Mode B
    model_b, plan_b = build_model_for_strategy(freeze_encoder=False)
    summary_b = trainable_parameter_summary(model_b)
    details["mode_b"] = {"plan": plan_b.description, **summary_b}

    if not encoder_requires_grad(model_b):
        issues.append("Mode B: encoder should be trainable")
        checks.append("FAIL: Mode B encoder trainable")
    else:
        checks.append("PASS: Mode B encoder trainable")

    if not classifier_requires_grad(model_b):
        issues.append("Mode B: classifier should be trainable")
        checks.append("FAIL: Mode B classifier trainable")
    else:
        checks.append("PASS: Mode B classifier trainable")

    if summary_b["trainable"] != summary_b["total"]:
        issues.append(
            f"Mode B: expected all params trainable, "
            f"trainable={summary_b['trainable']} total={summary_b['total']}"
        )
        checks.append("FAIL: Mode B all parameters trainable")
    else:
        checks.append("PASS: Mode B all parameters trainable")

    # Mode A
    model_a, plan_a = build_model_for_strategy(freeze_encoder=True)
    summary_a = trainable_parameter_summary(model_a)
    details["mode_a"] = {"plan": plan_a.description, **summary_a}

    if encoder_requires_grad(model_a):
        issues.append("Mode A: encoder should be frozen (requires_grad=False)")
        checks.append("FAIL: Mode A encoder frozen")
    else:
        checks.append("PASS: Mode A encoder frozen")

    if not classifier_requires_grad(model_a):
        issues.append("Mode A: classifier should remain trainable")
        checks.append("FAIL: Mode A classifier trainable")
    else:
        checks.append("PASS: Mode A classifier trainable")

    if summary_a["encoder_trainable"] != 0:
        issues.append(
            f"Mode A: encoder_trainable={summary_a['encoder_trainable']} expected 0"
        )
        checks.append("FAIL: Mode A encoder_trainable == 0")
    else:
        checks.append("PASS: Mode A encoder_trainable == 0")

    if summary_a["trainable"] != summary_a["head_trainable"]:
        issues.append(
            "Mode A: trainable params should equal classification-head params only"
        )
        checks.append("FAIL: Mode A trains head only")
    else:
        checks.append(
            f"PASS: Mode A trains head only ({summary_a['trainable']:,} params)"
        )

    # Switching strategies on the same instance
    apply_fine_tuning_strategy(model_b, freeze_encoder=True)
    if encoder_requires_grad(model_b):
        issues.append("apply_fine_tuning_strategy(freeze=True) did not freeze encoder")
        checks.append("FAIL: runtime switch to Mode A")
    else:
        checks.append("PASS: runtime switch to Mode A")

    apply_fine_tuning_strategy(model_b, freeze_encoder=False)
    if not encoder_requires_grad(model_b):
        issues.append("apply_fine_tuning_strategy(freeze=False) did not unfreeze encoder")
        checks.append("FAIL: runtime switch to Mode B")
    else:
        checks.append("PASS: runtime switch to Mode B")

    return len(issues) == 0, issues, checks, details


def run_fine_tuning_verification(
    output_dir: Optional[str] = None,
    *,
    stop_on_failure: bool = True,
) -> dict:
    from xlsr.experiment_dirs import create_experiment_dirs
    from xlsr.paths import DEFAULT_OUTPUT_DIR

    exp = create_experiment_dirs(output_dir or DEFAULT_OUTPUT_DIR)
    ok, issues, checks, details = verify_fine_tuning_modes()

    lines = [
        "Fine-Tuning Strategy Verification (Section 10)",
        "=" * 60,
        f"Status: {'PASSED' if ok else 'FAILED'}",
        "",
        "Modes:",
        "  Mode A — Frozen encoder (--freeze_encoder): train head only",
        "  Mode B — Full fine-tuning (DEFAULT): train encoder + head",
        "",
        "CLI rule:",
        "  with    --freeze_encoder  -> Mode A",
        "  without --freeze_encoder  -> Mode B",
        "",
        "Details:",
        f"  mode_b: {details.get('mode_b')}",
        f"  mode_a: {details.get('mode_a')}",
        "",
        "Checks:",
    ]
    for c in checks:
        lines.append(f"  - {c}")
    if issues:
        lines.append("")
        lines.append("Issues:")
        for i in issues:
            lines.append(f"  - {i}")
    else:
        lines.append("")
        lines.append("Fine-tuning modes behave as specified.")

    report_path = exp["metrics"] / "fine_tuning_verification.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Fine-tuning report written: %s", report_path)

    result = {"ok": ok, "issues": issues, "checks": checks, "details": details}
    if stop_on_failure and not ok:
        raise RuntimeError(
            "FINE-TUNING VERIFICATION FAILED — stopping.\n"
            + "\n".join(f"  - {i}" for i in issues)
        )
    return result
