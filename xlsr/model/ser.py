"""
Wav2Vec2-XLS-R-300M SER architecture.

Pipeline:
  input_values → Wav2Vec2Model encoder → last_hidden_state
               → masked mean pooling → dropout → Linear(hidden → 8 logits)
"""

from __future__ import annotations

import logging
from typing import Optional

import torch
import torch.nn as nn
from transformers import Wav2Vec2Model
from transformers.modeling_outputs import SequenceClassifierOutput

from xlsr.core.constants import MODEL_NAME
from xlsr.data.labels import NUM_CLASSES
from xlsr.model.loader import load_hf_token, load_xlsr_encoder
from xlsr.model.pooling import masked_mean_pooling

logger = logging.getLogger(__name__)

DEFAULT_DROPOUT = 0.3


class Wav2Vec2XLSRForSER(nn.Module):
    """Pretrained Wav2Vec2-XLS-R-300M encoder + SER classification head."""

    def __init__(
        self,
        encoder: Wav2Vec2Model,
        num_classes: int = NUM_CLASSES,
        dropout: float = DEFAULT_DROPOUT,
        freeze_encoder: bool = False,
    ) -> None:
        super().__init__()
        if num_classes != NUM_CLASSES:
            raise ValueError(
                f"This experiment requires num_classes={NUM_CLASSES}, got {num_classes}"
            )

        self.encoder = encoder
        self.num_classes = num_classes
        self.dropout_p = float(dropout)
        hidden_size = int(encoder.config.hidden_size)

        self.dropout = nn.Dropout(self.dropout_p)
        self.classifier = nn.Linear(hidden_size, num_classes)

        if freeze_encoder:
            self.freeze_encoder_parameters()

        logger.info(
            "Wav2Vec2XLSRForSER ready | hidden_size=%d | num_classes=%d | "
            "dropout=%.2f | freeze_encoder=%s",
            hidden_size,
            num_classes,
            self.dropout_p,
            freeze_encoder,
        )

    @property
    def hidden_size(self) -> int:
        return int(self.encoder.config.hidden_size)

    def freeze_encoder_parameters(self) -> None:
        for param in self.encoder.parameters():
            param.requires_grad = False
        logger.info("Encoder parameters frozen (train classification head only)")

    def unfreeze_encoder_parameters(self) -> None:
        for param in self.encoder.parameters():
            param.requires_grad = True
        logger.info("Encoder parameters unfrozen (full fine-tuning)")

    def _feature_vector_attention_mask(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor],
    ) -> torch.Tensor:
        batch, time, _ = hidden_states.shape
        if attention_mask is None:
            return torch.ones(
                batch,
                time,
                device=hidden_states.device,
                dtype=torch.long,
            )

        if hasattr(self.encoder, "_get_feature_vector_attention_mask"):
            return self.encoder._get_feature_vector_attention_mask(
                time, attention_mask
            )

        if attention_mask.size(1) == time:
            return attention_mask
        if attention_mask.size(1) > time:
            return attention_mask[:, :time]
        pad = time - attention_mask.size(1)
        return nn.functional.pad(attention_mask, (0, pad), value=0)

    def forward(
        self,
        input_values: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
    ) -> SequenceClassifierOutput:
        outputs = self.encoder(
            input_values=input_values,
            attention_mask=attention_mask,
            return_dict=True,
        )
        hidden_states = outputs.last_hidden_state

        feat_mask = self._feature_vector_attention_mask(hidden_states, attention_mask)
        pooled = masked_mean_pooling(hidden_states, feat_mask)
        logits = self.classifier(self.dropout(pooled))

        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits, labels)

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=None,
            attentions=None,
        )

    def count_parameters(self) -> dict:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        encoder = sum(p.numel() for p in self.encoder.parameters())
        head = sum(p.numel() for p in self.classifier.parameters()) + sum(
            p.numel() for p in self.dropout.parameters()
        )
        return {
            "total": total,
            "trainable": trainable,
            "encoder": encoder,
            "classifier": head,
            "hidden_size": self.hidden_size,
            "num_classes": self.num_classes,
        }


def build_xlsr_ser_model(
    model_name: str = MODEL_NAME,
    num_classes: int = NUM_CLASSES,
    dropout: float = DEFAULT_DROPOUT,
    freeze_encoder: bool = False,
    token: Optional[str] = None,
) -> Wav2Vec2XLSRForSER:
    """Load pretrained XLS-R encoder from Hub and attach SER head."""
    if model_name != MODEL_NAME:
        raise ValueError(f"Must use exactly '{MODEL_NAME}', got '{model_name}'")

    encoder = load_xlsr_encoder(model_name=model_name, token=token)
    return Wav2Vec2XLSRForSER(
        encoder=encoder,
        num_classes=num_classes,
        dropout=dropout,
        freeze_encoder=freeze_encoder,
    )
