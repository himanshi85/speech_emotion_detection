"""
Utilities for loading Hugging Face tokens and checkpoints.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from ser.core.paths import PROJECT_ROOT

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
        logger.info(
            "No HF_TOKEN found in %s or environment. Public model access will be used.",
            path,
        )
        return None

    logger.info("HF_TOKEN loaded from environment / %s", path.name)
    return token
