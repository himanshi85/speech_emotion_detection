"""Batch collators for waveform and MFCC models."""

from __future__ import annotations

import os
from typing import Any, Dict, List

import torch
from transformers import AutoFeatureExtractor

from ser.features.mfcc import MFCCExtractor
from ser.models.loader import load_hf_token


def _encode_waveforms(
    feature_extractor: Any,
    waveforms: List,
    sampling_rate: int = 16000,
) -> Dict[str, torch.Tensor]:
    import numpy as np

    arrays = [
        w.detach().cpu().numpy().squeeze() if isinstance(w, torch.Tensor) else np.asarray(w, dtype=np.float32).squeeze()
        for w in waveforms
    ]
    return feature_extractor(
        arrays,
        sampling_rate=sampling_rate,
        return_tensors="pt",
        padding=True,
        return_attention_mask=True,
    )


class WaveformCollator:
    def __init__(self, hub_id: str, token: str | None = None) -> None:
        if token is None:
            token = load_hf_token()
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(hub_id, token=token)

    def __call__(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        waveforms = [item["waveform"] for item in batch]
        encoded = _encode_waveforms(self.feature_extractor, waveforms)
        labels = torch.tensor([item.get("label", 0) for item in batch], dtype=torch.long)
        meta = {
            "filepath": [item.get("filepath", "") for item in batch],
            "filename": [item.get("filename", "") for item in batch],
            "actor_id": [item.get("actor_id", 0) for item in batch],
            "emotion": [item.get("emotion", "") for item in batch],
            "split": batch[0].get("split", "test") if batch else "test",
        }
        return {
            "input_values": encoded["input_values"],
            "attention_mask": encoded.get("attention_mask"),
            "labels": labels,
            "meta": meta,
        }


class MFCCCollator:
    def __init__(self) -> None:
        self.extractor = MFCCExtractor()

    def __call__(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        mfccs = []
        lengths = []
        for item in batch:
            wf = torch.tensor(item["waveform"], dtype=torch.float32)
            mfcc = self.extractor(wf)
            mfccs.append(mfcc)
            lengths.append(mfcc.size(1))

        max_len = max(lengths)
        n_mfcc = mfccs[0].size(0)
        padded = torch.zeros(len(batch), n_mfcc, max_len)
        mask = torch.zeros(len(batch), max_len, dtype=torch.long)
        for i, mfcc in enumerate(mfccs):
            t = mfcc.size(1)
            padded[i, :, :t] = mfcc
            mask[i, :t] = 1

        labels = torch.tensor([item.get("label", 0) for item in batch], dtype=torch.long)
        meta = {
            "filepath": [item.get("filepath", "") for item in batch],
            "filename": [item.get("filename", "") for item in batch],
            "actor_id": [item.get("actor_id", 0) for item in batch],
            "emotion": [item.get("emotion", "") for item in batch],
            "split": batch[0].get("split", "test") if batch else "test",
        }
        return {
            "mfcc": padded,
            "attention_mask": mask,
            "labels": labels,
            "meta": meta,
        }
