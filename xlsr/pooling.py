"""
Section 8 — Masked mean pooling over temporal encoder states.

Pools last_hidden_state while ignoring padded time steps.

    pooled = masked_mean(hidden_states, attention_mask)

Do NOT average padded values.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import torch

logger = logging.getLogger(__name__)


def masked_mean_pooling(
    hidden_states: torch.Tensor,
    attention_mask: torch.Tensor,
) -> torch.Tensor:
    """
    Mean-pool over time, ignoring padded frames.

    Args:
        hidden_states: (batch, time, hidden)
        attention_mask: (batch, time) with 1 = valid, 0 = pad
    Returns:
        pooled: (batch, hidden)
    """
    if attention_mask.dim() != 2:
        raise ValueError(f"attention_mask must be (B, T), got {tuple(attention_mask.shape)}")
    if hidden_states.dim() != 3:
        raise ValueError(f"hidden_states must be (B, T, H), got {tuple(hidden_states.shape)}")
    if hidden_states.size(0) != attention_mask.size(0) or hidden_states.size(1) != attention_mask.size(1):
        raise ValueError(
            "Shape mismatch: "
            f"hidden_states={tuple(hidden_states.shape)} "
            f"attention_mask={tuple(attention_mask.shape)}"
        )

    mask = attention_mask.to(dtype=hidden_states.dtype).unsqueeze(-1)  # (B, T, 1)
    summed = (hidden_states * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-9)
    return summed / counts


@dataclass
class PoolingVerificationReport:
    ok: bool
    issues: List[str] = field(default_factory=list)
    checks: List[str] = field(default_factory=list)


def _allclose(a: torch.Tensor, b: torch.Tensor, tol: float = 1e-5) -> bool:
    return torch.allclose(a, b, atol=tol, rtol=tol)


def verify_masked_mean_pooling() -> PoolingVerificationReport:
    """Unit checks proving padding is excluded from the temporal mean."""
    issues: List[str] = []
    checks: List[str] = []

    # Check 1: full mask == ordinary mean
    hidden = torch.tensor([[[1.0, 10.0], [3.0, 30.0], [5.0, 50.0]]])
    full_mask = torch.ones(1, 3, dtype=torch.long)
    pooled = masked_mean_pooling(hidden, full_mask)
    expected = hidden.mean(dim=1)
    if _allclose(pooled, expected):
        checks.append("PASS: full mask matches ordinary temporal mean")
    else:
        issues.append(f"Full-mask pool mismatch: got {pooled.tolist()} expected {expected.tolist()}")
        checks.append("FAIL: full mask matches ordinary temporal mean")

    # Check 2: trailing pad ignored
    hidden2 = torch.tensor([[[2.0, 4.0], [6.0, 8.0], [1000.0, 1000.0]]])
    mask2 = torch.tensor([[1, 1, 0]], dtype=torch.long)
    pooled2 = masked_mean_pooling(hidden2, mask2)
    expected2 = torch.tensor([[4.0, 6.0]])
    naive2 = hidden2.mean(dim=1)

    if _allclose(pooled2, expected2):
        checks.append("PASS: trailing pad ignored (mask=[1,1,0])")
    else:
        issues.append(f"Trailing-pad pool mismatch: got {pooled2.tolist()} expected {expected2.tolist()}")
        checks.append("FAIL: trailing pad ignored")

    if not _allclose(pooled2, naive2):
        checks.append("PASS: masked mean differs from naive mean when padding present")
    else:
        issues.append("Masked mean incorrectly equals naive mean — padding was averaged in")
        checks.append("FAIL: masked vs naive mean differ with padding")

    # Check 3: middle frames only
    hidden3 = torch.tensor([[[9.0, 9.0], [1.0, 2.0], [3.0, 4.0], [9.0, 9.0]]])
    mask3 = torch.tensor([[0, 1, 1, 0]], dtype=torch.long)
    pooled3 = masked_mean_pooling(hidden3, mask3)
    expected3 = torch.tensor([[2.0, 3.0]])
    if _allclose(pooled3, expected3):
        checks.append("PASS: middle frames only (mask=[0,1,1,0])")
    else:
        issues.append(f"Middle-mask pool mismatch: got {pooled3.tolist()} expected {expected3.tolist()}")
        checks.append("FAIL: middle frames only")

    # Check 4: batched variable masks
    hidden4 = torch.tensor(
        [
            [[1.0, 1.0], [3.0, 3.0], [0.0, 0.0]],
            [[2.0, 4.0], [0.0, 0.0], [0.0, 0.0]],
        ]
    )
    mask4 = torch.tensor([[1, 1, 0], [1, 0, 0]], dtype=torch.long)
    pooled4 = masked_mean_pooling(hidden4, mask4)
    expected4 = torch.tensor([[2.0, 2.0], [2.0, 4.0]])
    if _allclose(pooled4, expected4):
        checks.append("PASS: batched variable-length masks")
    else:
        issues.append(f"Batched pool mismatch: got {pooled4.tolist()} expected {expected4.tolist()}")
        checks.append("FAIL: batched variable-length masks")

    # Check 5: shape contract
    try:
        masked_mean_pooling(torch.zeros(2, 5), torch.ones(2, 5, dtype=torch.long))
        issues.append("Expected ValueError for 2D hidden_states, but none raised")
        checks.append("FAIL: rejects invalid hidden_states rank")
    except ValueError:
        checks.append("PASS: rejects invalid hidden_states rank")

    # Check 6: real encoder, padded batch vs single item
    try:
        from xlsr.audio_input import load_raw_waveform
        from xlsr.dataset_io import load_ravdess_splits
        from xlsr.model import build_xlsr_ser_model
        from xlsr.paths import DEFAULT_DATA_DIR
        from xlsr.processor import get_xlsr_processor, waveforms_to_model_inputs

        model = build_xlsr_ser_model()
        model.eval()
        processor = get_xlsr_processor()
        bundle = load_ravdess_splits(DEFAULT_DATA_DIR)
        paths = bundle.train["abs_filepath"].head(2).tolist()
        raws = [load_raw_waveform(p) for p in paths]
        encoded = waveforms_to_model_inputs(processor, raws, padding=True)

        with torch.no_grad():
            outputs = model.encoder(
                input_values=encoded["input_values"],
                attention_mask=encoded["attention_mask"],
                return_dict=True,
            )
            hidden = outputs.last_hidden_state
            feat_mask = model._feature_vector_attention_mask(
                hidden, encoded["attention_mask"]
            )
            pooled = masked_mean_pooling(hidden, feat_mask)

            enc0 = waveforms_to_model_inputs(processor, raws[0], padding=False)
            out0 = model.encoder(
                input_values=enc0["input_values"],
                attention_mask=enc0.get("attention_mask"),
                return_dict=True,
            )
            h0 = out0.last_hidden_state
            m0 = model._feature_vector_attention_mask(h0, enc0.get("attention_mask"))
            pooled0 = masked_mean_pooling(h0, m0)

        if _allclose(pooled[0:1], pooled0, tol=1e-4):
            checks.append("PASS: padded batch item matches single-item pool (real XLS-R states)")
        else:
            max_diff = (pooled[0:1] - pooled0).abs().max().item()
            issues.append(
                f"Padded-batch pool differs from single-item pool (max_diff={max_diff:.6f})"
            )
            checks.append("FAIL: padded batch vs single-item consistency")

        if pooled.shape == (2, model.hidden_size):
            checks.append(f"PASS: real forward pooled shape {(2, model.hidden_size)}")
        else:
            issues.append(f"Unexpected pooled shape {tuple(pooled.shape)}")
            checks.append("FAIL: real forward pooled shape")
    except Exception as exc:  # noqa: BLE001
        issues.append(f"End-to-end pooling check failed: {exc}")
        checks.append("FAIL: end-to-end real encoder pooling")

    return PoolingVerificationReport(ok=len(issues) == 0, issues=issues, checks=checks)


def run_pooling_verification(
    output_dir: Optional[str] = None,
    *,
    stop_on_failure: bool = True,
) -> PoolingVerificationReport:
    from xlsr.experiment_dirs import create_experiment_dirs
    from xlsr.paths import DEFAULT_OUTPUT_DIR

    exp = create_experiment_dirs(output_dir or DEFAULT_OUTPUT_DIR)
    report = verify_masked_mean_pooling()

    lines = [
        "Masked Mean Pooling Verification (Section 8)",
        "=" * 60,
        f"Status: {'PASSED' if report.ok else 'FAILED'}",
        "",
        "Requirement:",
        "  pooled = masked_mean(hidden_states, attention_mask)",
        "  Do not simply average padded values.",
        "",
        "Checks:",
    ]
    for c in report.checks:
        lines.append(f"  - {c}")
    if report.issues:
        lines.append("")
        lines.append("Issues:")
        for i in report.issues:
            lines.append(f"  - {i}")
    else:
        lines.append("")
        lines.append("Masked mean pooling correctly ignores padded frames.")

    report_path = exp["metrics"] / "pooling_verification.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Pooling report written: %s", report_path)

    if stop_on_failure and not report.ok:
        raise RuntimeError(
            "POOLING VERIFICATION FAILED — stopping.\n"
            + "\n".join(f"  - {i}" for i in report.issues)
        )
    return report
