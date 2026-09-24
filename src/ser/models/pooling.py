"""
Masked mean pooling and verification for temporal encoder representations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

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

    mask = attention_mask.to(dtype=hidden_states.dtype).unsqueeze(-1)
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
    issues: List[str] = []
    checks: List[str] = []

    # 1. Full mask
    hidden = torch.tensor([[[1.0, 10.0], [3.0, 30.0], [5.0, 50.0]]])
    full_mask = torch.ones(1, 3, dtype=torch.long)
    pooled = masked_mean_pooling(hidden, full_mask)
    expected = hidden.mean(dim=1)
    if _allclose(pooled, expected):
        checks.append("PASS: full mask matches ordinary temporal mean")
    else:
        issues.append(f"Full-mask pool mismatch: got {pooled.tolist()} expected {expected.tolist()}")
        checks.append("FAIL: full mask matches ordinary temporal mean")

    # 2. Trailing pad
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

    # 3. Middle frames
    hidden3 = torch.tensor([[[9.0, 9.0], [1.0, 2.0], [3.0, 4.0], [9.0, 9.0]]])
    mask3 = torch.tensor([[0, 1, 1, 0]], dtype=torch.long)
    pooled3 = masked_mean_pooling(hidden3, mask3)
    expected3 = torch.tensor([[2.0, 3.0]])
    if _allclose(pooled3, expected3):
        checks.append("PASS: middle frames only (mask=[0,1,1,0])")
    else:
        issues.append(f"Middle-mask pool mismatch: got {pooled3.tolist()} expected {expected3.tolist()}")
        checks.append("FAIL: middle frames only")

    # 4. Batched variable length
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

    # 5. Invalid dimensions
    try:
        masked_mean_pooling(torch.zeros(2, 5), torch.ones(2, 5, dtype=torch.long))
        issues.append("Expected ValueError for 2D hidden_states, but none raised")
        checks.append("FAIL: rejects invalid hidden_states rank")
    except ValueError:
        checks.append("PASS: rejects invalid hidden_states rank")

    return PoolingVerificationReport(ok=len(issues) == 0, issues=issues, checks=checks)
