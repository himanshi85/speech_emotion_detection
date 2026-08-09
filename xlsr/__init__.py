"""Wav2Vec2-XLS-R-300M SER package."""

from xlsr.audio_input import AudioInputError, load_raw_waveform, run_audio_input_verification
from xlsr.constants import MODEL_NAME, NUM_CLASSES, SAMPLE_RATE
from xlsr.dataset_io import load_ravdess_splits
from xlsr.experiment_dirs import create_experiment_dirs
from xlsr.labels import (
    CLASS_NAMES,
    EMOTION_TO_ID,
    ID_TO_EMOTION,
    LabelMappingError,
    assert_emotion_classes,
    num_classifier_logits,
    run_label_verification,
)
from xlsr.classification_head import run_head_verification
from xlsr.config import default_config, load_config, save_config
from xlsr.fine_tuning import (
    FineTuningMode,
    apply_fine_tuning_strategy,
    build_model_for_strategy,
    resolve_fine_tuning_mode,
    run_fine_tuning_verification,
)
from xlsr.pooling import masked_mean_pooling, run_pooling_verification
from xlsr.model import Wav2Vec2XLSRForSER, build_xlsr_ser_model
from xlsr.model_loader import (
    load_hf_token,
    load_xlsr_encoder,
    load_xlsr_feature_extractor,
    load_xlsr_from_hub,
)
from xlsr.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.processor import (
    get_xlsr_processor,
    run_processor_verification,
    waveforms_to_model_inputs,
)
from xlsr.dataset import RAVDESSXLSRDataset, SERDataCollator
from xlsr.metrics import compute_ser_metrics, save_confusion_matrix
from xlsr.trainer import XLSRTrainer

__all__ = [
    "MODEL_NAME",
    "NUM_CLASSES",
    "SAMPLE_RATE",
    "CLASS_NAMES",
    "EMOTION_TO_ID",
    "ID_TO_EMOTION",
    "DEFAULT_DATA_DIR",
    "DEFAULT_OUTPUT_DIR",
    "load_hf_token",
    "load_xlsr_encoder",
    "load_xlsr_feature_extractor",
    "load_xlsr_from_hub",
    "load_ravdess_splits",
    "create_experiment_dirs",
    "ActorLeakageError",
    "assert_no_actor_leakage",
    "run_split_guard",
    "LabelMappingError",
    "assert_emotion_classes",
    "num_classifier_logits",
    "run_label_verification",
    "AudioInputError",
    "load_raw_waveform",
    "run_audio_input_verification",
    "get_xlsr_processor",
    "waveforms_to_model_inputs",
    "run_processor_verification",
    "Wav2Vec2XLSRForSER",
    "build_xlsr_ser_model",
    "masked_mean_pooling",
    "run_pooling_verification",
    "run_head_verification",
    "FineTuningMode",
    "resolve_fine_tuning_mode",
    "apply_fine_tuning_strategy",
    "build_model_for_strategy",
    "run_fine_tuning_verification",
    "default_config",
    "load_config",
    "save_config",
    "RAVDESSXLSRDataset",
    "SERDataCollator",
    "XLSRTrainer",
    "compute_ser_metrics",
]

