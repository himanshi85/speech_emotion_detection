"""Model registry and builders."""

from __future__ import annotations

from typing import Any, Dict

from ser.data.collators import MFCCCollator, WaveformCollator
from ser.models.base import BaseSERModel
from ser.models.mfcc_cnn_bilstm import MFCCCNNBiLSTMModel
from ser.models.mfcc_lstm import MFCCLSTMModel
from ser.models.transformer import TransformerSERModel
from xlsr.model.loader import load_hf_token

# Verified HuggingFace hub IDs and expected parameter scales
HUB_IDS: Dict[str, Dict[str, Any]] = {
    "mfcc_lstm": {
        "display_name": "MFCC + LSTM",
        "input_type": "mfcc",
        "expected_params": "~800K",
        "architecture": "MFCC(40) -> LSTM(256x2) -> Linear(8)",
    },
    "mfcc_cnn_bilstm": {
        "display_name": "MFCC + CNN-BiLSTM",
        "input_type": "mfcc",
        "expected_params": "~900K",
        "architecture": "MFCC -> CNN(64,128,256) -> BiLSTM(128x2) -> Linear(8)",
    },
    "wav2vec2_xlsr_300m": {
        "hub_id": "facebook/wav2vec2-xls-r-300m",
        "display_name": "Wav2Vec2-XLS-R-300M",
        "input_type": "waveform",
        "encoder_class": "Wav2Vec2Model",
        "hidden_size": 1024,
        "expected_params": "~315M",
        "architecture": "XLS-R-300M -> masked pool -> Dropout -> Linear(8)",
    },
    "wav2vec2": {
        "hub_id": "facebook/wav2vec2-base",
        "display_name": "Wav2Vec2-base",
        "input_type": "waveform",
        "encoder_class": "Wav2Vec2Model",
        "hidden_size": 768,
        "expected_params": "~94M",
        "architecture": "Wav2Vec2-base -> masked pool -> Dropout -> Linear(8)",
    },
    "hubert": {
        "hub_id": "facebook/hubert-base-ls960",
        "display_name": "HuBERT-base",
        "input_type": "waveform",
        "encoder_class": "HubertModel",
        "hidden_size": 768,
        "expected_params": "~94M",
        "architecture": "HuBERT -> masked pool -> Dropout -> Linear(8)",
    },
    "wavlm": {
        "hub_id": "microsoft/wavlm-base-plus",
        "display_name": "WavLM-base-plus",
        "input_type": "waveform",
        "encoder_class": "WavLMModel",
        "hidden_size": 768,
        "expected_params": "~94M",
        "architecture": "WavLM -> masked pool -> Dropout -> Linear(8)",
    },
    "emotion2vec_plus": {
        "hub_id": "emotion2vec/emotion2vec_plus_base",
        "display_name": "emotion2vec+ (FunASR backbone)",
        "input_type": "waveform",
        "model_backend": "funasr",
        "hidden_size": 768,
        "expected_params": "~90M",
        "architecture": "emotion2vec+ base via FunASR -> fine-tune head",
        "note": "Uses emotion2vec/emotion2vec_plus_base (~90M). Requires funasr package.",
        "fallback_hub_id": "facebook/wav2vec2-base",
    },
    "beats": {
        "hub_id": "microsoft/wavlm-base-plus",
        "display_name": "BEATs (WavLM acoustic proxy)",
        "input_type": "waveform",
        "encoder_class": "WavLMModel",
        "hidden_size": 768,
        "expected_params": "~94M",
        "architecture": "WavLM-base-plus proxy for BEATs-style acoustic SSL",
        "note": (
            "Official Microsoft BEATs uses fbank+Transformer and is not on HF Transformers. "
            "This config uses WavLM-base-plus as the comparable acoustic SSL backbone. "
            "Set beats_checkpoint_path in config for true BEATs weights."
        ),
    },
}


def build_model(cfg: Dict[str, Any]) -> BaseSERModel:
    key = cfg["model_key"]
    dropout = float(cfg.get("dropout", 0.3))
    freeze = bool(cfg.get("freeze_encoder", False))
    token = load_hf_token()

    if key == "mfcc_lstm":
        return MFCCLSTMModel(
            n_mfcc=int(cfg.get("n_mfcc", 40)),
            hidden_size=int(cfg.get("lstm_hidden", 256)),
            num_layers=int(cfg.get("lstm_layers", 2)),
            dropout=dropout,
        )
    if key == "mfcc_cnn_bilstm":
        return MFCCCNNBiLSTMModel(
            n_mfcc=int(cfg.get("n_mfcc", 40)),
            lstm_hidden=int(cfg.get("lstm_hidden", 128)),
            lstm_layers=int(cfg.get("lstm_layers", 2)),
            dropout=dropout,
        )

    meta = HUB_IDS.get(key, {})
    hub_id = cfg.get("hub_id") or meta.get("hub_id")

    # emotion2vec+: prefer real hub; fallback only if funasr missing
    if key == "emotion2vec_plus" and cfg.get("model_backend") == "funasr":
        try:
            from ser.models.emotion2vec import Emotion2VecSERModel
            return Emotion2VecSERModel(
                hub_id=hub_id,
                dropout=dropout,
                freeze_encoder=freeze,
            )
        except ImportError:
            hub_id = meta.get("fallback_hub_id", hub_id)

    trust = bool(cfg.get("trust_remote_code", meta.get("trust_remote_code", False)))
    return TransformerSERModel(
        hub_id=hub_id,
        model_key=key,
        dropout=dropout,
        freeze_encoder=freeze,
        token=token,
        trust_remote_code=trust,
    )


def build_collator(cfg: Dict[str, Any]):
    key = cfg["model_key"]
    meta = HUB_IDS.get(key, {})
    input_type = cfg.get("input_type") or meta.get("input_type", "waveform")
    if input_type == "mfcc":
        return MFCCCollator()
    hub_id = cfg.get("hub_id") or meta.get("hub_id")
    if key == "emotion2vec_plus" and cfg.get("model_backend") == "funasr":
        hub_id = meta.get("fallback_hub_id", "facebook/wav2vec2-base")
    return WaveformCollator(hub_id=hub_id)
