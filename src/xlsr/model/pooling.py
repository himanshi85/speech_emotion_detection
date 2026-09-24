"""Masked mean pooling over temporal encoder states."""

from __future__ import annotations

import torch


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
