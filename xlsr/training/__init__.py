"""Training utilities: fine-tuning modes, trainer, metrics, and experiment directories."""

from xlsr.training.experiment import create_experiment_dirs
from xlsr.training.fine_tuning import (
    FineTuningMode,
    FineTuningPlan,
    add_freeze_encoder_argument,
    apply_fine_tuning_strategy,
    build_model_for_strategy,
    resolve_fine_tuning_mode,
    trainable_parameter_summary,
)
from xlsr.training.metrics import (
    compute_ser_metrics,
    plot_training_curves,
    save_classification_report,
    save_confusion_matrix,
    save_test_predictions,
)
from xlsr.training.trainer import XLSRTrainer, get_device

__all__ = [
    "create_experiment_dirs",
    "FineTuningMode",
    "FineTuningPlan",
    "add_freeze_encoder_argument",
    "apply_fine_tuning_strategy",
    "build_model_for_strategy",
    "resolve_fine_tuning_mode",
    "trainable_parameter_summary",
    "compute_ser_metrics",
    "plot_training_curves",
    "save_classification_report",
    "save_confusion_matrix",
    "save_test_predictions",
    "XLSRTrainer",
    "get_device",
]
