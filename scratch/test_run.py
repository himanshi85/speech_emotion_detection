import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import traceback
from xlsr.dataset_io import load_ravdess_splits
from xlsr.dataset import RAVDESSXLSRDataset
from xlsr.trainer import XLSRTrainer
from xlsr.config import default_config

try:
    b = load_ravdess_splits("ravdess_preprocessed")
    tr = RAVDESSXLSRDataset(b.train, max_samples=4)
    va = RAVDESSXLSRDataset(b.validation, max_samples=4)
    c = default_config(freeze_encoder=True)
    c["num_epochs"] = 1
    c["batch_size"] = 2
    t = XLSRTrainer(c, "outputs/test_run")
    t.run_training(tr, va)
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
