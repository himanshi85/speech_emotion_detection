"""Class weights for imbalanced RAVDESS emotions."""

from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from xlsr.data.labels import NUM_CLASSES


def compute_class_weights(train_df: pd.DataFrame) -> torch.Tensor:
    counts = np.zeros(NUM_CLASSES, dtype=np.float64)
    for label in train_df["label"]:
        counts[int(label)] += 1
    counts = np.maximum(counts, 1.0)
    weights = len(train_df) / (NUM_CLASSES * counts)
    return torch.tensor(weights, dtype=torch.float32)
