"""Fine-tuning strategy verification runner."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from xlsr.core.paths import DEFAULT_OUTPUT_DIR
from xlsr.model.ser import Wav2Vec2XLSRForSER
from xlsr.training.experiment import create_experiment_dirs
from xlsr.training.fine_tuning import (
    FineTuningMode,
    apply_fine_tuning_strategy,
    build_model_for_strategy,
    classifier_requires_grad,
    encoder_requires_grad,
    resolve_fine_tuning_mode,
    trainable_parameter_summary,
)

logger = logging.getLogger(__name__)


def verify_fine_tuning_modes() -> Tuple[bool, List[str], List[str], dict]:
    issues: List[str] = []
    checks: List[str] = []
    details: dict = {}

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
) -> Dict:
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
