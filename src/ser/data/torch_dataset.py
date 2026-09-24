"""PyTorch Dataset for RAVDESS SER."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd
import torch
from torch.utils.data import Dataset

from ser.data.audio import load_raw_waveform


class RAVDESSSERDataset(Dataset):
    def __init__(self, df: pd.DataFrame, split_name: str) -> None:
        self.df = df.reset_index(drop=True)
        self.split_name = split_name

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        row = self.df.iloc[idx]
        path = Path(row["abs_filepath"])
        raw = load_raw_waveform(path)
        return {
            "waveform": raw.waveform,
            "label": int(row["label"]),
            "emotion": str(row["emotion"]),
            "filepath": str(path),
            "filename": str(row["filename"]),
            "actor_id": int(row["actor_id"]),
            "split": self.split_name,
        }
