"""XLS-R model, processor, and pooling."""

from xlsr.model.loader import (
    load_hf_token,
    load_xlsr_config,
    load_xlsr_encoder,
    load_xlsr_feature_extractor,
    load_xlsr_from_hub,
)
from xlsr.model.pooling import masked_mean_pooling
from xlsr.model.processor import (
    ProcessorBundle,
    encode_audio_file,
    get_xlsr_processor,
    summarize_model_inputs,
    waveforms_to_model_inputs,
)
from xlsr.model.ser import (
    DEFAULT_DROPOUT,
    Wav2Vec2XLSRForSER,
    build_xlsr_ser_model,
)

__all__ = [
    "load_hf_token",
    "load_xlsr_config",
    "load_xlsr_encoder",
    "load_xlsr_feature_extractor",
    "load_xlsr_from_hub",
    "masked_mean_pooling",
    "ProcessorBundle",
    "encode_audio_file",
    "get_xlsr_processor",
    "summarize_model_inputs",
    "waveforms_to_model_inputs",
    "DEFAULT_DROPOUT",
    "Wav2Vec2XLSRForSER",
    "build_xlsr_ser_model",
]
