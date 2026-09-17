"""emotion2vec+ SER model via FunASR backbone + trainable classification head."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import torch
import torch.nn as nn

from ser.models.base import BaseSERModel
from xlsr.data.labels import NUM_CLASSES

logger = logging.getLogger(__name__)

EMOTION2VEC_HUB = "emotion2vec/emotion2vec_plus_base"
HIDDEN_SIZE = 768


class Emotion2VecSERModel(BaseSERModel):
    """
    Wraps FunASR emotion2vec+ encoder and adds an 8-class RAVDESS head.

    The FunASR model is used for feature extraction; only the classification
    head is trained unless freeze_encoder=False and backbone supports gradients.
    """

    input_type = "waveform"
    model_key = "emotion2vec_plus"

    def __init__(
        self,
        hub_id: str = EMOTION2VEC_HUB,
        num_classes: int = NUM_CLASSES,
        dropout: float = 0.3,
        freeze_encoder: bool = False,
    ) -> None:
        super().__init__()
        try:
            from funasr import AutoModel
        except ImportError as exc:
            raise ImportError(
                "emotion2vec+ requires FunASR: pip install funasr"
            ) from exc

        self.hub_id = hub_id
        self._funasr = AutoModel(model=hub_id, hub="hf", disable_update=True)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(HIDDEN_SIZE, num_classes)
        self.freeze_encoder = freeze_encoder

        if freeze_encoder:
            for param in self._get_backbone_parameters():
                param.requires_grad = False

        logger.info("emotion2vec+ SER | hub=%s | head=%d classes", hub_id, num_classes)

    def _get_backbone_parameters(self):
        model = getattr(self._funasr, "model", None)
        if model is not None:
            return model.parameters()
        return []

    def count_parameters(self) -> Dict[str, int]:
        backbone = sum(p.numel() for p in self._get_backbone_parameters())
        head = sum(p.numel() for p in self.classifier.parameters()) + sum(
            p.numel() for p in self.dropout.parameters()
        )
        total = backbone + head
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {
            "total": total,
            "trainable": trainable,
            "frozen": total - trainable,
            "encoder": backbone,
            "head": head,
            "hidden_size": HIDDEN_SIZE,
            "num_classes": NUM_CLASSES,
        }

    def forward(
        self,
        input_values: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        class_weights: Optional[torch.Tensor] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # FunASR path not integrated for batched tensor training yet.
        # Fall back to zero features — use TransformerSERModel for full training.
        raise NotImplementedError(
            "emotion2vec+ FunASR fine-tuning is not yet integrated in the training loop. "
            "Set model_backend: transformer and hub_id: emotion2vec/emotion2vec_plus_base "
            "or use wav2vec2-base fallback in config."
        )
