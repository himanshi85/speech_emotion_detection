"""Generic transformer encoder + SER head (Wav2Vec2, HuBERT, WavLM, XLS-R)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import torch
import torch.nn as nn
from transformers import AutoModel, HubertModel, Wav2Vec2Model, WavLMModel

from ser.models.base import BaseSERModel
from xlsr.data.labels import NUM_CLASSES
from xlsr.model.pooling import masked_mean_pooling

logger = logging.getLogger(__name__)


def load_speech_encoder(
    hub_id: str,
    token: str | None = None,
    trust_remote_code: bool = False,
) -> nn.Module:
    """Load the correct HuggingFace encoder class for each backbone."""
    hub_lower = hub_id.lower()
    kwargs = {"token": token, "trust_remote_code": trust_remote_code}
    if "hubert" in hub_lower:
        return HubertModel.from_pretrained(hub_id, **kwargs)
    if "wavlm" in hub_lower:
        return WavLMModel.from_pretrained(hub_id, **kwargs)
    if "wav2vec2" in hub_lower or "xls-r" in hub_lower:
        return Wav2Vec2Model.from_pretrained(hub_id, **kwargs)
    return AutoModel.from_pretrained(hub_id, **kwargs)


class TransformerSERModel(BaseSERModel):
    input_type = "waveform"

    def __init__(
        self,
        hub_id: str,
        model_key: str,
        num_classes: int = NUM_CLASSES,
        dropout: float = 0.3,
        freeze_encoder: bool = False,
        token: str | None = None,
        trust_remote_code: bool = False,
    ) -> None:
        super().__init__()
        self.model_key = model_key
        self.hub_id = hub_id
        self.num_classes = num_classes
        self.dropout_p = dropout

        self.encoder = load_speech_encoder(hub_id, token=token, trust_remote_code=trust_remote_code)
        hidden_size = int(getattr(self.encoder.config, "hidden_size", 768))
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_classes)

        if freeze_encoder:
            for param in self.encoder.parameters():
                param.requires_grad = False

        logger.info(
            "%s ready | hub=%s | hidden=%d | head=%d | freeze=%s",
            model_key,
            hub_id,
            hidden_size,
            num_classes,
            freeze_encoder,
        )

    @property
    def hidden_size(self) -> int:
        return int(self.encoder.config.hidden_size)

    def count_parameters(self) -> Dict[str, int]:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        encoder = sum(p.numel() for p in self.encoder.parameters())
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
            "num_classes": self.num_classes,
        }

    def _feature_mask(self, hidden: torch.Tensor, attention_mask: Optional[torch.Tensor]) -> torch.Tensor:
        batch, time, _ = hidden.shape
        if attention_mask is None:
            return torch.ones(batch, time, device=hidden.device, dtype=torch.long)
        if hasattr(self.encoder, "_get_feature_vector_attention_mask"):
            return self.encoder._get_feature_vector_attention_mask(time, attention_mask)
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
        class_weights: Optional[torch.Tensor] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        outputs = self.encoder(
            input_values=input_values,
            attention_mask=attention_mask,
            return_dict=True,
        )
        hidden = outputs.last_hidden_state
        feat_mask = self._feature_mask(hidden, attention_mask)
        pooled = masked_mean_pooling(hidden, feat_mask)
        logits = self.classifier(self.dropout(pooled))

        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits, labels, weight=class_weights)

        return {"loss": loss, "logits": logits}
