"""
Constants for the Wav2Vec2-XLS-R-300M SER experiment.

Do NOT substitute this model with wav2vec2-base, HuBERT, WavLM, etc.
Emotion IDs are locked in xlsr.labels (Section 4) — do not change them.
"""

from xlsr.labels import (
    CLASS_NAMES,
    EMOTION_TO_ID,
    ID_TO_EMOTION,
    NUM_CLASSES,
)

# Exact Hugging Face Hub model ID (Section 1)
MODEL_NAME = "facebook/wav2vec2-xls-r-300m"

# Audio expected by XLS-R / preprocessing
SAMPLE_RATE = 16000
NUM_CHANNELS = 1

__all__ = [
    "MODEL_NAME",
    "SAMPLE_RATE",
    "NUM_CHANNELS",
    "NUM_CLASSES",
    "EMOTION_TO_ID",
    "ID_TO_EMOTION",
    "CLASS_NAMES",
]
