"""
Model and audio constants for the XLS-R SER experiment.

Label IDs live in xlsr.data.labels (import separately to avoid import cycles).
"""

MODEL_NAME = "facebook/wav2vec2-xls-r-300m"
SAMPLE_RATE = 16000
NUM_CHANNELS = 1

__all__ = ["MODEL_NAME", "SAMPLE_RATE", "NUM_CHANNELS"]
