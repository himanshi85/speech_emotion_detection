"""MFCC + LSTM classical baseline."""

from __future__ import annotations

from typing import Any, Dict, Optional

import torch
import torch.nn as nn

from ser.models.base import BaseSERModel
from xlsr.data.labels import NUM_CLASSES
from xlsr.model.pooling import masked_mean_pooling


class MFCCLSTMModel(BaseSERModel):
    model_key = "mfcc_lstm"
    input_type = "mfcc"

    def __init__(
        self,
        n_mfcc: int = 40,
        hidden_size: int = 256,
        num_layers: int = 2,
        num_classes: int = NUM_CLASSES,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_mfcc,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_classes)
        self.hidden_size = hidden_size
        self.n_mfcc = n_mfcc

    def count_parameters(self) -> Dict[str, int]:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        encoder = sum(p.numel() for p in self.lstm.parameters())
        head = sum(p.numel() for p in self.classifier.parameters()) + sum(
            p.numel() for p in self.dropout.parameters()
        )
        return {
            "total": total,
            "trainable": trainable,
            "frozen": total - trainable,
            "encoder": encoder,
            "head": head,
            "hidden_size": self.hidden_size,
            "num_classes": NUM_CLASSES,
        }

    def forward(
        self,
        mfcc: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        class_weights: Optional[torch.Tensor] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # mfcc: (B, n_mfcc, T) -> LSTM expects (B, T, F)
        x = mfcc.transpose(1, 2)
        out, _ = self.lstm(x)
        if attention_mask is None:
            pooled = out[:, -1, :]
        else:
            pooled = masked_mean_pooling(out, attention_mask)
        logits = self.classifier(self.dropout(pooled))
        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits, labels, weight=class_weights)
        return {"loss": loss, "logits": logits}
