"""Classification head verification runner."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import torch
import torch.nn as nn

from xlsr.core.paths import DEFAULT_OUTPUT_DIR
from xlsr.data.labels import NUM_CLASSES
from xlsr.model.ser import DEFAULT_DROPOUT, Wav2Vec2XLSRForSER, build_xlsr_ser_model
from xlsr.training.experiment import create_experiment_dirs

logger = logging.getLogger(__name__)


@dataclass
class HeadVerificationReport:
    ok: bool
    issues: List[str] = field(default_factory=list)
    checks: List[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


def verify_classification_head(
    model: Optional[Wav2Vec2XLSRForSER] = None,
) -> HeadVerificationReport:
    issues: List[str] = []
    checks: List[str] = []
    details: dict = {}

    if model is None:
        model = build_xlsr_ser_model()

    if not isinstance(model.dropout, nn.Dropout):
        issues.append(f"Expected nn.Dropout, got {type(model.dropout)}")
        checks.append("FAIL: dropout module type")
    else:
        checks.append("PASS: dropout module is nn.Dropout")

    if not isinstance(model.classifier, nn.Linear):
        issues.append(f"Expected nn.Linear classifier, got {type(model.classifier)}")
        checks.append("FAIL: classifier is Linear")
    else:
        checks.append("PASS: classifier is nn.Linear")

    p = float(model.dropout.p)
    details["dropout_p"] = p
    if abs(p - DEFAULT_DROPOUT) > 1e-9:
        issues.append(f"dropout p={p}, expected {DEFAULT_DROPOUT}")
        checks.append("FAIL: dropout == 0.3")
    else:
        checks.append("PASS: dropout == 0.3")

    in_f = int(model.classifier.in_features)
    out_f = int(model.classifier.out_features)
    details["in_features"] = in_f
    details["out_features"] = out_f
    details["hidden_size"] = model.hidden_size

    if in_f != model.hidden_size:
        issues.append(
            f"Linear in_features={in_f} != encoder hidden_size={model.hidden_size}"
        )
        checks.append("FAIL: Linear(hidden_size → 8) input dim")
    else:
        checks.append(f"PASS: Linear in_features == hidden_size ({in_f})")

    if out_f != NUM_CLASSES:
        issues.append(f"Linear out_features={out_f}, expected {NUM_CLASSES}")
        checks.append("FAIL: Linear output == 8 logits")
    else:
        checks.append("PASS: Linear out_features == 8")

    expected_params = in_f * out_f + out_f
    actual_params = sum(p.numel() for p in model.classifier.parameters())
    details["classifier_params"] = actual_params
    if actual_params != expected_params:
        issues.append(
            f"Classifier params={actual_params}, expected {expected_params} for simple Linear"
        )
        checks.append("FAIL: simple Linear parameter count")
    else:
        checks.append(f"PASS: simple Linear param count ({actual_params})")

    forbidden = ("lm_head", "ctc", "projector", "mlp", "classifier2")
    named = dict(model.named_children())
    details["top_level_modules"] = sorted(named.keys())
    for name in forbidden:
        if name in named:
            issues.append(f"Unexpected complex/ASR module present: {name}")
    if not any(n in named for n in forbidden):
        checks.append("PASS: no CTC/ASR/extra MLP head modules")
    else:
        checks.append("FAIL: unexpected head modules")

    required = {"encoder", "dropout", "classifier"}
    if not required.issubset(set(named.keys())):
        issues.append(f"Missing modules: {sorted(required - set(named.keys()))}")
        checks.append("FAIL: required modules present")
    else:
        checks.append("PASS: modules are encoder + dropout + classifier only")

    extras = set(named.keys()) - required
    details["extra_modules"] = sorted(extras)
    if extras:
        issues.append(f"Extra top-level modules beyond simple head design: {sorted(extras)}")
        checks.append("FAIL: only simple head attached")
    else:
        checks.append("PASS: only encoder + dropout + classifier")

    model.train()
    torch.manual_seed(0)
    pooled = torch.randn(4, model.hidden_size)

    with torch.no_grad():
        y1 = model.classifier(model.dropout(pooled))
        y2 = model.classifier(model.dropout(pooled))
        model.eval()
        y_eval = model.classifier(model.dropout(pooled))
        y_eval2 = model.classifier(model.dropout(pooled))

    if not torch.allclose(y_eval, y_eval2):
        issues.append("In eval mode, dropout+classifier outputs should be deterministic")
        checks.append("FAIL: eval-mode determinism")
    else:
        checks.append("PASS: eval-mode dropout is inactive (deterministic)")

    if y_eval.shape != (4, NUM_CLASSES):
        issues.append(f"Head output shape {tuple(y_eval.shape)} != {(4, NUM_CLASSES)}")
        checks.append("FAIL: head output shape (B, 8)")
    else:
        checks.append("PASS: head output shape (B, 8)")

    if torch.allclose(y1, y2):
        differs = False
        model.train()
        with torch.no_grad():
            base = model.classifier(model.dropout(pooled))
            for _ in range(10):
                if not torch.allclose(base, model.classifier(model.dropout(pooled))):
                    differs = True
                    break
        if differs:
            checks.append("PASS: train-mode dropout is stochastic before Linear")
        else:
            issues.append("Dropout appears inactive in train mode")
            checks.append("FAIL: train-mode dropout stochasticity")
    else:
        checks.append("PASS: train-mode dropout is stochastic before Linear")

    details["logits_shape"] = (4, NUM_CLASSES)
    details["formula"] = f"Dropout({DEFAULT_DROPOUT}) -> Linear({in_f} -> {NUM_CLASSES})"

    return HeadVerificationReport(
        ok=len(issues) == 0,
        issues=issues,
        checks=checks,
        details=details,
    )


def run_head_verification(
    output_dir: Optional[str] = None,
    *,
    stop_on_failure: bool = True,
) -> HeadVerificationReport:
    exp = create_experiment_dirs(output_dir or DEFAULT_OUTPUT_DIR)
    report = verify_classification_head()

    lines = [
        "Classification Head Verification (Section 9)",
        "=" * 60,
        f"Status: {'PASSED' if report.ok else 'FAILED'}",
        "",
        "Design:",
        f"  Dropout({DEFAULT_DROPOUT}) -> Linear(hidden_size -> {NUM_CLASSES})",
        "  Keep head simple to evaluate pretrained XLS-R representation.",
        "",
        "Details:",
    ]
    for k, v in report.details.items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("Checks:")
    for c in report.checks:
        lines.append(f"  - {c}")
    if report.issues:
        lines.append("")
        lines.append("Issues:")
        for i in report.issues:
            lines.append(f"  - {i}")
    else:
        lines.append("")
        lines.append("Classification head matches Section 9 requirements.")

    report_path = exp["metrics"] / "classification_head_verification.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Classification head report written: %s", report_path)

    if stop_on_failure and not report.ok:
        raise RuntimeError(
            "CLASSIFICATION HEAD VERIFICATION FAILED — stopping.\n"
            + "\n".join(f"  - {i}" for i in report.issues)
        )
    return report
