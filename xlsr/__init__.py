"""
XLS-R Speech Emotion Recognition (SER) Package.

Modular hierarchical architecture:
    xlsr.core      — Paths, constants, configuration
    xlsr.data      — Audio loaders, datasets, label mappings, split validation
    xlsr.model     — XLS-R SER architectures, processor, pooling, Hub loader
    xlsr.training  — Experiment directories, fine-tuning utilities, trainer, metrics
    xlsr.verify    — Architecture, split, and label verification runners
"""

from __future__ import annotations

import sys
from xlsr import core, data, model, training, verify

# Re-export subpackage modules
from xlsr.core import config, constants, paths
from xlsr.data import audio, dataset, labels, split

__version__ = "0.3.0"

# Dynamic module aliases for seamless backward compatibility
sys.modules.setdefault("xlsr.constants", constants)
sys.modules.setdefault("xlsr.paths", paths)
sys.modules.setdefault("xlsr.config", config)
sys.modules.setdefault("xlsr.dataset", dataset)
sys.modules.setdefault("xlsr.dataset_io", dataset)
sys.modules.setdefault("xlsr.labels", labels)
sys.modules.setdefault("xlsr.split_guard", split)
sys.modules.setdefault("xlsr.audio_input", audio)
sys.modules.setdefault("xlsr.model_loader", model.loader)
sys.modules.setdefault("xlsr.pooling", model.pooling)
sys.modules.setdefault("xlsr.processor", model.processor)
sys.modules.setdefault("xlsr.experiment_dirs", training.experiment)
sys.modules.setdefault("xlsr.fine_tuning", training.fine_tuning)
sys.modules.setdefault("xlsr.metrics", training.metrics)
sys.modules.setdefault("xlsr.trainer", training.trainer)

__all__ = [
    "core",
    "data",
    "model",
    "training",
    "verify",
    "__version__",
]
