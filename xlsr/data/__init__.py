"""Dataset loading, labels, audio I/O, and split validation."""

from xlsr.data.audio import (
    AudioInputError,
    AudioVerificationReport,
    RawWaveform,
    collect_split_audio_paths,
    load_raw_waveform,
    verify_audio_paths,
)
from xlsr.data.dataset import (
    DatasetBundle,
    DatasetIntegrityError,
    DatasetNotFoundError,
    load_full_metadata,
    load_ravdess_splits,
    verify_actor_independent_split,
    write_dataset_summary,
)
from xlsr.data.labels import (
    CLASS_NAMES,
    EMOTION_TO_ID,
    ID_TO_EMOTION,
    LabelMappingError,
    NUM_CLASSES,
    assert_emotion_classes,
    emotion_to_id,
    id_to_emotion,
    num_classifier_logits,
    verify_emotion_classes,
)
from xlsr.data.split import (
    ActorLeakageError,
    SplitVerificationReport,
    assert_no_actor_leakage,
    verify_dataset_split,
)

__all__ = [
    "AudioInputError",
    "AudioVerificationReport",
    "RawWaveform",
    "collect_split_audio_paths",
    "load_raw_waveform",
    "verify_audio_paths",
    "DatasetBundle",
    "DatasetIntegrityError",
    "DatasetNotFoundError",
    "load_full_metadata",
    "load_ravdess_splits",
    "verify_actor_independent_split",
    "write_dataset_summary",
    "CLASS_NAMES",
    "EMOTION_TO_ID",
    "ID_TO_EMOTION",
    "LabelMappingError",
    "NUM_CLASSES",
    "assert_emotion_classes",
    "emotion_to_id",
    "id_to_emotion",
    "num_classifier_logits",
    "verify_emotion_classes",
    "ActorLeakageError",
    "SplitVerificationReport",
    "assert_no_actor_leakage",
    "verify_dataset_split",
]
