"""Verification runners for each implementation section."""

from xlsr.verify.architecture import run_architecture_verification
from xlsr.verify.audio import run_audio_input_verification
from xlsr.verify.fine_tuning import run_fine_tuning_verification
from xlsr.verify.head import run_head_verification
from xlsr.verify.labels import run_label_verification
from xlsr.verify.pooling import run_pooling_verification
from xlsr.verify.processor import run_processor_verification
from xlsr.verify.split import run_split_guard

__all__ = [
    "run_architecture_verification",
    "run_audio_input_verification",
    "run_fine_tuning_verification",
    "run_head_verification",
    "run_label_verification",
    "run_pooling_verification",
    "run_processor_verification",
    "run_split_guard",
]
