# Speech Emotion Recognition — Multi-Model Comparison on RAVDESS

8-class emotion recognition comparing classical baselines and pretrained speech encoders on the actor-independent RAVDESS split.

## Models

| Key | Model |
|-----|-------|
| `mfcc_lstm` | MFCC + LSTM |
| `mfcc_cnn_bilstm` | MFCC + CNN-BiLSTM |
| `wav2vec2_xlsr_300m` | Wav2Vec2-XLS-R-300M |
| `wav2vec2` | Wav2Vec2-base |
| `hubert` | HuBERT-base |
| `wavlm` | WavLM-base-plus |
| `emotion2vec_plus` | emotion2vec+ (set `hub_id` in config) |
| `beats` | BEATs (set `hub_id` in config) |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `HF_TOKEN` for Hugging Face downloads.

## Train one model

```bash
python scripts/train.py --model hubert
python scripts/train.py --model mfcc_lstm --epochs 80
python scripts/train.py --model wav2vec2_xlsr_300m --freeze_encoder
```

## Train all models

```bash
python scripts/train_all.py
python scripts/train_all.py --skip beats emotion2vec_plus
```

## Evaluate checkpoint

```bash
python scripts/evaluate.py --model hubert --checkpoint best
```

## Compare all results

After training, merge metrics and plots:

```bash
python scripts/compare_results.py
```

Output: `outputs/comparison/`

## Per-model outputs

Each model writes to `outputs/<model_key>/`:

```text
checkpoints/best_model/model.pt
metrics/training_history.csv
metrics/loss_curve.png
metrics/macro_f1_curve.png
metrics/accuracy_curve.png
metrics/final_results.csv
predictions/train|validation|test/
  predictions.csv
  classification_report.csv
  confusion_matrix.csv
  confusion_matrix.png
```

## Verify pipeline (xlsr sections 1–10)

```bash
python -m xlsr verify all
pytest
```

## Project layout

```text
speech/
├── configs/           # YAML per model
├── scripts/           # train, evaluate, compare
├── ser/               # Multi-model training framework
├── xlsr/              # XLS-R verification package
├── ravdess_preprocessed/
└── outputs/
    ├── <model_key>/   # Per-model results
    └── comparison/    # Combined tables & curves
```

## Research rules

- Actor-independent split (do not re-split)
- Locked 8-class label mapping
- Best checkpoint = highest **validation Macro-F1**
- Test set evaluated once on best checkpoint only
