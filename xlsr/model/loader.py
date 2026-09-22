"""
Load facebook/wav2vec2-xls-r-300m from the Hugging Face Hub.

Uses HF_TOKEN from the project .env file when present.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv
from transformers import AutoFeatureExtractor, Wav2Vec2Config, Wav2Vec2Model

from xlsr.core.constants import MODEL_NAME, SAMPLE_RATE
from xlsr.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

ENV_PATH = PROJECT_ROOT / ".env"


def load_hf_token(env_path: Optional[Path] = None) -> Optional[str]:
    """Load Hugging Face token from .env (HF_TOKEN) or the environment."""
    path = Path(env_path) if env_path is not None else ENV_PATH
    load_dotenv(dotenv_path=path, override=False)

    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    if token is not None:
        token = token.strip()
    if not token:
        logger.warning(
            "No HF_TOKEN found in %s or environment. "
            "Public model download may still work; set HF_TOKEN for authenticated access.",
            path,
        )
        return None

    logger.info("HF_TOKEN loaded from environment / %s", path.name)
    return token


def load_xlsr_feature_extractor(
    model_name: str = MODEL_NAME,
    token: Optional[str] = None,
) -> AutoFeatureExtractor:
    if token is None:
        token = load_hf_token()

    logger.info("Loading feature extractor from Hugging Face: %s", model_name)
    extractor = AutoFeatureExtractor.from_pretrained(model_name, token=token)

    sr = getattr(extractor, "sampling_rate", None)
    if sr is not None and int(sr) != SAMPLE_RATE:
        raise ValueError(
            f"Feature extractor sampling_rate={sr}, expected {SAMPLE_RATE}"
        )

    return extractor


def load_xlsr_encoder(
    model_name: str = MODEL_NAME,
    token: Optional[str] = None,
) -> Wav2Vec2Model:
    if model_name != MODEL_NAME:
        raise ValueError(
            f"This experiment must use exactly '{MODEL_NAME}'. Got: '{model_name}'"
        )

    if token is None:
        token = load_hf_token()

    logger.info("Loading Wav2Vec2Model encoder from Hugging Face: %s", model_name)
    model = Wav2Vec2Model.from_pretrained(model_name, token=token)
    model.eval()

    hidden_size = int(model.config.hidden_size)
    logger.info(
        "Loaded %s | hidden_size=%d | params=%s",
        model_name,
        hidden_size,
        f"{sum(p.numel() for p in model.parameters()):,}",
    )
    return model


def load_xlsr_config(
    model_name: str = MODEL_NAME,
    token: Optional[str] = None,
) -> Wav2Vec2Config:
    if token is None:
        token = load_hf_token()

    logger.info("Loading config from Hugging Face: %s", model_name)
    return Wav2Vec2Config.from_pretrained(model_name, token=token)


def load_xlsr_from_hub(
    model_name: str = MODEL_NAME,
    token: Optional[str] = None,
    load_weights: bool = True,
) -> Tuple[Optional[Wav2Vec2Model], AutoFeatureExtractor, Wav2Vec2Config]:
    if model_name != MODEL_NAME:
        raise ValueError(
            f"This experiment must use exactly '{MODEL_NAME}'. Got: '{model_name}'"
        )

    if token is None:
        token = load_hf_token()

    config = load_xlsr_config(model_name=model_name, token=token)
    feature_extractor = load_xlsr_feature_extractor(model_name=model_name, token=token)
    model = None
    if load_weights:
        model = load_xlsr_encoder(model_name=model_name, token=token)

    return model, feature_extractor, config
