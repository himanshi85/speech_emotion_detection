"""
Section 7 — Wav2Vec2-XLS-R-300M SER architecture.

Pipeline:
  input_values → Wav2Vec2Model encoder → last_hidden_state
               → masked mean pooling → dropout → Linear(hidden → 8 logits)

Emotion classification only — no ASR/CTC head.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
import torch.nn as nn
from transformers import Wav2Vec2Model
from transformers.modeling_outputs import SequenceClassifierOutput

from xlsr.constants import MODEL_NAME
from xlsr.labels import NUM_CLASSES
from xlsr.model_loader import load_hf_token, load_xlsr_encoder
from xlsr.pooling import masked_mean_pooling

logger = logging.getLogger(__name__)

DEFAULT_DROPOUT = 0.3


class Wav2Vec2XLSRForSER(nn.Module):
    """
    Pretrained Wav2Vec2-XLS-R-300M encoder + SER classification head.

    Not a CTC/ASR model. Outputs 8 emotion logits.
    """

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
        """Reduce waveform-level mask to encoder hidden-state time steps."""
        batch, time, _ = hidden_states.shape
        if attention_mask is None:
            return torch.ones(
                batch,
                time,
                device=hidden_states.device,
                dtype=torch.long,
            )

        # Prefer official Wav2Vec2 helper when available
        if hasattr(self.encoder, "_get_feature_vector_attention_mask"):
            return self.encoder._get_feature_vector_attention_mask(
                time, attention_mask
            )

        # Fallback: truncate/pad mask length to match hidden time
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
        hidden_states = outputs.last_hidden_state  # (B, T, H)

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
    # load_xlsr_encoder sets eval(); training loop will switch modes later
    model = Wav2Vec2XLSRForSER(
        encoder=encoder,
        num_classes=num_classes,
        dropout=dropout,
        freeze_encoder=freeze_encoder,
    )
    return model


@dataclass
class ArchitectureVerificationResult:
    ok: bool
    logits_shape: Tuple[int, ...]
    param_counts: dict
    issues: list


def run_architecture_verification(
    output_dir: Optional[str] = None,
    *,
    batch_size: int = 2,
    freeze_encoder: bool = False,
    stop_on_failure: bool = True,
) -> ArchitectureVerificationResult:
    """
    Build the SER model, run a tiny forward pass, write report under outputs/.
    """
    from xlsr.audio_input import load_raw_waveform
    from xlsr.dataset_io import load_ravdess_splits
    from xlsr.experiment_dirs import create_experiment_dirs
    from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
    from xlsr.processor import get_xlsr_processor, waveforms_to_model_inputs

    out_root = output_dir or str(DEFAULT_OUTPUT_DIR)
    exp = create_experiment_dirs(out_root)
    issues = []

    model = build_xlsr_ser_model(freeze_encoder=freeze_encoder)
    model.eval()
    counts = model.count_parameters()

    processor = get_xlsr_processor()
    bundle = load_ravdess_splits(DEFAULT_DATA_DIR)
    paths = bundle.train["abs_filepath"].head(batch_size).tolist()
    raws = [load_raw_waveform(p) for p in paths]
    encoded = waveforms_to_model_inputs(processor, raws, padding=True)

    with torch.no_grad():
        out = model(
            input_values=encoded["input_values"],
            attention_mask=encoded.get("attention_mask"),
        )

    logits = out.logits
    logits_shape = tuple(logits.shape)
    expected = (batch_size, NUM_CLASSES)
    if logits_shape != expected:
        issues.append(f"logits shape {logits_shape} != expected {expected}")
    if logits_shape[-1] != NUM_CLASSES:
        issues.append(f"Model must output {NUM_CLASSES} logits, got {logits_shape[-1]}")

    # Ensure no CTC head attributes
    if hasattr(model, "lm_head"):
        issues.append("Unexpected ASR/CTC lm_head found on SER model")

    ok = len(issues) == 0
    lines = [
        "Wav2Vec2-XLS-R-300M SER Architecture Verification (Section 7)",
        "=" * 60,
        f"Status: {'PASSED' if ok else 'FAILED'}",
        f"Encoder: Wav2Vec2Model ({MODEL_NAME})",
        "Head: Dropout -> Linear(hidden_size -> 8)  [no CTC/ASR]",
        "Pooling: masked mean over temporal dimension",
        "",
        f"hidden_size: {counts['hidden_size']}",
        f"num_classes (logits): {counts['num_classes']}",
        f"dropout: {DEFAULT_DROPOUT}",
        f"freeze_encoder: {freeze_encoder}",
        f"logits_shape: {logits_shape}",
        "",
        "Parameters:",
        f"  total:     {counts['total']:,}",
        f"  trainable: {counts['trainable']:,}",
        f"  encoder:   {counts['encoder']:,}",
        f"  classifier:{counts['classifier']:,}",
        "",
        "Forward path:",
        "  input_values -> Wav2Vec2Model -> last_hidden_state",
        "  -> masked_mean_pooling -> dropout -> linear -> 8 logits",
    ]
    if issues:
        lines.append("")
        lines.append("Issues:")
        for i in issues:
            lines.append(f"  - {i}")

    report_path = exp["metrics"] / "architecture_verification.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Architecture report written: %s", report_path)

    result = ArchitectureVerificationResult(
        ok=ok,
        logits_shape=logits_shape,
        param_counts=counts,
        issues=issues,
    )
    if stop_on_failure and not ok:
        raise RuntimeError(
            "ARCHITECTURE VERIFICATION FAILED\n"
            + "\n".join(f"  - {i}" for i in issues)
        )
    return result
