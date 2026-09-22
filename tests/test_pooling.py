"""Unit tests for masked mean pooling."""

from __future__ import annotations

import torch

from xlsr.model.pooling import masked_mean_pooling
from xlsr.verify.pooling import verify_masked_mean_pooling


def test_masked_mean_ignores_padding() -> None:
    hidden = torch.tensor([[[2.0, 4.0], [6.0, 8.0], [1000.0, 1000.0]]])
    mask = torch.tensor([[1, 1, 0]], dtype=torch.long)
    pooled = masked_mean_pooling(hidden, mask)
    expected = torch.tensor([[4.0, 6.0]])
    assert torch.allclose(pooled, expected)


def test_verification_suite_passes() -> None:
    report = verify_masked_mean_pooling()
    assert report.ok
