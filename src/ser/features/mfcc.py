"""MFCC feature extraction for classical baselines."""

from __future__ import annotations

import torch
import torchaudio

SAMPLE_RATE = 16000
N_MFCC = 40
N_FFT = 512
HOP_LENGTH = 160


class MFCCExtractor:
    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        n_mfcc: int = N_MFCC,
        n_fft: int = N_FFT,
        hop_length: int = HOP_LENGTH,
    ) -> None:
        self.transform = torchaudio.transforms.MFCC(
            sample_rate=sample_rate,
            n_mfcc=n_mfcc,
            log_mels=True,
            melkwargs={
                "n_fft": n_fft,
                "hop_length": hop_length,
                "n_mels": 128,
                "center": True,
            },
        )

    def __call__(self, waveform: torch.Tensor) -> torch.Tensor:
        """waveform: (samples,) -> mfcc: (n_mfcc, time)"""
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)
        mfcc = self.transform(waveform)
        return mfcc.squeeze(0)
