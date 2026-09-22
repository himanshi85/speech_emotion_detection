"""
PyTorch Dataset and Dynamic DataCollator for Wav2Vec2-XLS-R-300M SER.

Section 13 (Variable-Length Audio) & Section 14 (Dataset Class).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from xlsr.audio_input import load_raw_waveform
from xlsr.constants import SAMPLE_RATE
from xlsr.processor import ProcessorBundle, waveforms_to_model_inputs

logger = logging.getLogger(__name__)


class RAVDESSXLSRDataset(Dataset):
    """
    PyTorch Dataset for preprocessed RAVDESS metadata.

    Loads raw 16 kHz mono WAV audio waveforms and mapped 8-class emotion labels.
    Preserves original filenames and actor IDs for evaluation/debugging.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        data_dir: Optional[Union[Path, str]] = None,
        max_samples: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.df = df.reset_index(drop=True)
        if max_samples is not None and max_samples > 0:
            self.df = self.df.iloc[:max_samples].reset_index(drop=True)

        self.data_dir = Path(data_dir).resolve() if data_dir else None

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        row = self.df.iloc[idx]
        filepath = str(row["abs_filepath"]) if "abs_filepath" in row else str(row["filepath"])
        
        # Load raw audio waveform (16000 Hz, mono)
        audio = load_raw_waveform(filepath, expected_sr=SAMPLE_RATE)
        
        return {
            "waveform": audio.waveform,  # 1D float32 numpy array
            "label": int(row["label"]),
            "filename": str(row["filename"]),
            "actor_id": int(row["actor_id"]),
            "emotion": str(row["emotion"]),
            "filepath": filepath,
        }


class SERDataCollator:
    """
    Custom collator for dynamic padding of variable-length audio waveforms.

    Pads waveforms dynamically within each batch to produce:
      - input_values (B, max_length)
      - attention_mask (B, max_length)
      - labels (B,)
    """

    def __init__(self, processor: ProcessorBundle) -> None:
        self.processor = processor

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        waveforms = [item["waveform"] for item in features]
        labels = [item["label"] for item in features]

        # Convert waveforms into padded model inputs
        batch_inputs = waveforms_to_model_inputs(
            self.processor,
            waveforms=waveforms,
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )

        batch_inputs["labels"] = torch.tensor(labels, dtype=torch.long)
        return batch_inputs
