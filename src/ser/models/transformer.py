"""Generic transformer encoder + SER head (Wav2Vec2, HuBERT, WavLM, XLS-R)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import torch
import torch.nn as nn
from transformers import AutoModel, HubertModel, Wav2Vec2Model, WavLMModel

from ser.models.base import BaseSERModel
from ser.data.labels import NUM_CLASSES
from ser.models.pooling import masked_mean_pooling

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


class WeightedLayerPooling(nn.Module):
    """Learnable layer-wise weighted sum across transformer hidden layers (SUPERB style)."""

    def __init__(self, num_layers: int = 12) -> None:
        super().__init__()
        self.num_layers = num_layers
        self.weights = nn.Parameter(torch.ones(num_layers))

    def forward(self, hidden_states: tuple[torch.Tensor, ...] | list[torch.Tensor]) -> torch.Tensor:
        # hidden_states contains (layer_0_embedding, layer_1, ..., layer_N)
        n_avail = len(hidden_states)
        if n_avail < self.num_layers:
            selected = list(hidden_states)
            weights = self.weights[:len(selected)]
        else:
            selected = list(hidden_states[-self.num_layers:])
            weights = self.weights[-len(selected):]
        stacked = torch.stack(selected, dim=0)  # (L, B, T, D)
        norm_weights = nn.functional.softmax(weights, dim=0).view(-1, 1, 1, 1)
        return (stacked * norm_weights).sum(dim=0)  # (B, T, D)


class TransformerSERModel(BaseSERModel):
    input_type = "waveform"

    def __init__(
        self,
        hub_id: str,
        model_key: str,
        num_classes: int = NUM_CLASSES,
        dropout: float = 0.3,
        freeze_encoder: bool = False,
        layer_pooling: str = "last",
        token: str | None = None,
        trust_remote_code: bool = False,
    ) -> None:
        super().__init__()
        self.model_key = model_key
        self.hub_id = hub_id
        self.num_classes = num_classes
        self.dropout_p = dropout
        self.layer_pooling = layer_pooling

        self.encoder = load_speech_encoder(hub_id, token=token, trust_remote_code=trust_remote_code)
        hidden_size = int(getattr(self.encoder.config, "hidden_size", 768))
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_classes)

        if self.layer_pooling == "weighted":
            num_layers = int(getattr(self.encoder.config, "num_hidden_layers", 12))
            self.weighted_pooler = WeightedLayerPooling(num_layers=num_layers)
        else:
            self.weighted_pooler = None

        if freeze_encoder:
            for param in self.encoder.parameters():
                param.requires_grad = False

        logger.info(
            "%s ready | hub=%s | hidden=%d | head=%d | pooling=%s | freeze=%s",
            model_key,
            hub_id,
            hidden_size,
            num_classes,
            layer_pooling,
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
        if self.weighted_pooler is not None:
            head += sum(p.numel() for p in self.weighted_pooler.parameters())
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
        output_hidden_states = (self.layer_pooling == "weighted")
        outputs = self.encoder(
            input_values=input_values,
            attention_mask=attention_mask,
            output_hidden_states=output_hidden_states,
            return_dict=True,
        )

        if self.layer_pooling == "weighted" and outputs.hidden_states is not None:
            hidden = self.weighted_pooler(outputs.hidden_states)
        else:
            hidden = outputs.last_hidden_state

        feat_mask = self._feature_mask(hidden, attention_mask)
        pooled = masked_mean_pooling(hidden, feat_mask)
        logits = self.classifier(self.dropout(pooled))

        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits, labels, weight=class_weights)

        return {"loss": loss, "logits": logits}
