"""Base SER model interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import torch
import torch.nn as nn


class BaseSERModel(nn.Module, ABC):
    model_key: str = "base"
    input_type: str = "waveform"

    @abstractmethod
    def forward(self, labels: Optional[torch.Tensor] = None, **kwargs: Any) -> Dict[str, Any]:
        ...

    def count_parameters(self) -> Dict[str, int]:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {"total": total, "trainable": trainable, "frozen": total - trainable}
