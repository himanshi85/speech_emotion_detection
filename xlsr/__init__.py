"""
Wav2Vec2-XLS-R-300M Speech Emotion Recognition on RAVDESS.

Package layout:
    xlsr.core      — paths, constants, config
    xlsr.data      — dataset, labels, audio, split guard
    xlsr.model     — SER model, processor, pooling, Hub loader
    xlsr.training  — fine-tuning modes, experiment dirs
    xlsr.verify    — section verification runners
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
