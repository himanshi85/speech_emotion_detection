"""Unit tests for masked mean pooling."""

from __future__ import annotations

import torch

from ser.models.pooling import masked_mean_pooling, verify_masked_mean_pooling


def test_masked_mean_ignores_padding() -> None:
    hidden = torch.tensor([[[2.0, 4.0], [6.0, 8.0], [1000.0, 1000.0]]])
    mask = torch.tensor([[1, 1, 0]], dtype=torch.long)
    pooled = masked_mean_pooling(hidden, mask)
    expected = torch.tensor([[4.0, 6.0]])
    assert torch.allclose(pooled, expected)


def test_verification_suite_passes() -> None:
    report = verify_masked_mean_pooling()
    assert report.ok


def test_weighted_layer_pooling() -> None:
    from ser.models.transformer import WeightedLayerPooling
    pooler = WeightedLayerPooling(num_layers=3)
    layer1 = torch.ones(2, 4, 8) * 1.0
    layer2 = torch.ones(2, 4, 8) * 2.0
    layer3 = torch.ones(2, 4, 8) * 3.0
    hidden_states = (layer1, layer2, layer3)
    out = pooler(hidden_states)
    assert out.shape == (2, 4, 8)
    # Equal initial weights: average of (1 + 2 + 3) / 3 = 2.0
    assert torch.allclose(out, torch.ones(2, 4, 8) * 2.0)
    # Test gradient backward
    loss = out.sum()
    loss.backward()
    assert pooler.weights.grad is not None

