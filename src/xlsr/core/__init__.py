"""Core configuration, paths, and experiment constants."""

from xlsr.core.constants import MODEL_NAME, NUM_CHANNELS, SAMPLE_RATE
from xlsr.core.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR, PROJECT_ROOT

__all__ = [
    "PROJECT_ROOT",
    "DEFAULT_DATA_DIR",
    "DEFAULT_OUTPUT_DIR",
    "MODEL_NAME",
    "SAMPLE_RATE",
    "NUM_CHANNELS",
]
