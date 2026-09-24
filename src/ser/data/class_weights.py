"""Class weights for imbalanced RAVDESS emotions."""

from __future__ import annotations

import numpy as np
import pandas as pd
import torch



def compute_class_weights(train_df: pd.DataFrame, num_classes: int | None = None) -> torch.Tensor:
    if num_classes is None:
        num_classes = int(train_df["label"].max() + 1)
    counts = np.zeros(num_classes, dtype=np.float64)
    for label in train_df["label"]:
        counts[int(label)] += 1
    counts = np.maximum(counts, 1.0)
    weights = len(train_df) / (num_classes * counts)
    return torch.tensor(weights, dtype=torch.float32)