"""MFCC + CNN-BiLSTM classical baseline."""

from __future__ import annotations

from typing import Any, Dict, Optional

import torch
import torch.nn as nn

from ser.models.base import BaseSERModel
from ser.data.labels import NUM_CLASSES
from ser.models.pooling import masked_mean_pooling


class MFCCCNNBiLSTMModel(BaseSERModel):
    model_key = "mfcc_cnn_bilstm"
    input_type = "mfcc"

    def __init__(
        self,
        n_mfcc: int = 40,
        cnn_channels: tuple = (64, 128, 256),
        lstm_hidden: int = 128,
        lstm_layers: int = 2,
        num_classes: int = NUM_CLASSES,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        layers = []
        in_ch = n_mfcc
        for ch in cnn_channels:
            layers.extend(
                [
                    nn.Conv1d(in_ch, ch, kernel_size=3, padding=1),
                    nn.ReLU(),
                    nn.BatchNorm1d(ch),
                ]
            )
            in_ch = ch
        self.cnn = nn.Sequential(*layers)
        self.lstm = nn.LSTM(
            input_size=cnn_channels[-1],
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if lstm_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(lstm_hidden * 2, num_classes)
        self.hidden_size = lstm_hidden * 2
        self.n_mfcc = n_mfcc

    def count_parameters(self) -> Dict[str, int]:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        encoder = sum(p.numel() for p in self.cnn.parameters()) + sum(
            p.numel() for p in self.lstm.parameters()
        )
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
        x = self.cnn(mfcc)
        x = x.transpose(1, 2)
        out, _ = self.lstm(x)
        if attention_mask is None:
            pooled = out.mean(dim=1)
        else:
            pooled = masked_mean_pooling(out, attention_mask)
        logits = self.classifier(self.dropout(pooled))
        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits, labels, weight=class_weights)
        return {"loss": loss, "logits": logits}
