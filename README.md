# Multi-Model Speech Emotion Recognition (SER) Framework

A modular, production-grade PyTorch benchmarking framework for **Speech Emotion Recognition (SER)** across diverse speech corpora. Compares classical acoustic baselines against state-of-the-art self-supervised foundation models with strict speaker-independent evaluation (zero actor leakage across splits).

---

## 📊 Benchmark Leaderboard

All evaluations are conducted strictly on **unseen actors** (disjoint speaker test partition).

### CREMA-D (91 Diverse Actors, 6 Emotion Classes)
*Random guessing baseline across 6 classes: 16.67%*

| Model / Method | Architecture / Backbone | Test Accuracy | Macro-F1 | UAR |
| :--- | :--- | :---: | :---: | :---: |
| **Multi-Model Ensemble** | **Soft-Voting (Top 5)** | **75.57%** | **0.7594** | **75.61%** |
| **HuBERT** | Acoustic Unit SSL (`facebook/hubert-base-ls960`) | **71.98%** | **0.7209** | **72.03%** |
| **Wav2Vec 2.0** | Contrastive SSL (`facebook/wav2vec2-base`) | **69.25%** | **0.6982** | **69.29%** |
| **emotion2vec+** | Emotion-Specialized Pretrained | **69.25%** | **0.6982** | **69.29%** |
| **WavLM** | Denoising SSL (`microsoft/wavlm-base-plus`) | **66.32%** | **0.6584** | **66.45%** |
| **MFCC + CNN-BiLSTM** | 2D CNN Spectrogram + BiLSTM + Attention | **63.30%** | **0.6392** | **63.24%** |
| **BEATs** | Acoustic Spectrogram Transformer | **62.64%** | **0.6190** | **62.89%** |
| **MFCC + LSTM** | Sequential Baseline | **59.62%** | **0.5999** | **59.69%** |
| **Wav2Vec2-XLS-R-300M** | Multilingual Frozen Backbone | **24.43%** | **0.1346** | **23.85%** |

### RAVDESS (24 Actors, 8 Emotion Classes)
*Random guessing baseline across 8 classes: 12.50%*

| Model / Method | Architecture / Backbone | Test Accuracy | Macro-F1 | UAR |
| :--- | :--- | :---: | :---: | :---: |
| **Multi-Model Ensemble** | **Soft-Voting (Top 3)** | **68.75%** | **0.6791** | **0.6875** |
| **WavLM** | Denoising SSL (`microsoft/wavlm-base-plus`) | **67.08%** | **0.6631** | **0.6708** |
| **Wav2Vec 2.0** | Contrastive SSL (`facebook/wav2vec2-base`) | **50.00%** | **0.4933** | **0.5000** |
| **emotion2vec+** | Emotion-Specialized Pretrained | **50.00%** | **0.4933** | **0.5000** |
| **MFCC + CNN-BiLSTM** | 2D CNN Spectrogram + BiLSTM + Attention | **42.50%** | **0.3984** | **0.4250** |
| **BEATs** | Acoustic Spectrogram Transformer | **34.58%** | **0.2466** | **0.3458** |
| **MFCC + LSTM** | Sequential Baseline | **32.92%** | **0.2817** | **0.3292** |
| **HuBERT** | Acoustic Unit SSL | **32.50%** | **0.2117** | **0.3250** |
| **Wav2Vec2-XLS-R-300M** | Multilingual Frozen Backbone | **13.33%** | **0.0294** | **0.1250** |

### SAVEE (4 Actors, 7 Emotion Classes)
*Random guessing baseline across 7 classes: 14.29%*

| Model / Method | Architecture / Backbone | Test Accuracy | Macro-F1 | UAR |
| :--- | :--- | :---: | :---: | :---: |
| **HuBERT** | Acoustic Unit SSL (`facebook/hubert-base-ls960`) | **25.83%** | **0.2435** | **25.83%** |
| **Wav2Vec 2.0** | Contrastive SSL (`facebook/wav2vec2-base`) | **25.83%** | **0.2526** | **25.83%** |
| **emotion2vec+** | Emotion-Specialized Pretrained | **25.83%** | **0.2285** | **25.83%** |
| **BEATs** | Acoustic Spectrogram Transformer | **25.00%** | **0.2412** | **25.00%** |
| **WavLM** | Denoising SSL (`microsoft/wavlm-base-plus`) | **25.00%** | **0.2312** | **25.00%** |
| **Multi-Model Ensemble** | **Soft-Voting (Top 6)** | **25.00%** | **0.2312** | **25.00%** |
| **MFCC + CNN-BiLSTM** | 2D CNN Spectrogram + BiLSTM + Attention | **25.00%** | **0.2458** | **25.00%** |
| **MFCC + LSTM** | Sequential Baseline | **21.67%** | **0.2185** | **21.67%** |
| **Wav2Vec2-XLS-R-300M** | Multilingual Frozen Backbone | **18.33%** | **0.1702** | **18.33%** |

### TESS (2 Female Actors, 7 Emotion Classes, 200 Target Words)
*Prompt-independent partition (zero word leakage on 30 unseen vocabulary words). Random baseline: 14.29%*

| Model / Method | Architecture / Backbone | Test Accuracy | Macro-F1 | UAR |
| :--- | :--- | :---: | :---: | :---: |
| **Multi-Model Ensemble** | **Soft-Voting (Top 5)** | **100.00%** | **1.0000** | **1.0000** |
| **HuBERT** | Acoustic Unit SSL (`facebook/hubert-base-ls960`) | **100.00%** | **1.0000** | **1.0000** |
| **Wav2Vec 2.0** | Contrastive SSL (`facebook/wav2vec2-base`) | **100.00%** | **1.0000** | **1.0000** |
| **WavLM** | Denoising SSL (`microsoft/wavlm-base-plus`) | **100.00%** | **1.0000** | **1.0000** |
| **emotion2vec+** | Emotion-Specialized Pretrained | **100.00%** | **1.0000** | **1.0000** |
| **MFCC + LSTM** | Sequential Baseline | **100.00%** | **1.0000** | **1.0000** |
| **MFCC + CNN-BiLSTM** | 2D CNN Spectrogram + BiLSTM + Attention | **99.76%** | **0.9976** | **0.9976** |
| **BEATs** | Acoustic Spectrogram Transformer | **99.76%** | **0.9976** | **0.9976** |
| **Wav2Vec2-XLS-R-300M** | Multilingual Frozen Backbone | **19.76%** | **0.0886** | **0.1976** |

---

## 📁 Repository Structure

```text
speech_emotion_detection-develop-v2/
├── configs/                     # Model architecture and hyperparameter configs
│   ├── _base.yaml               # Shared defaults (audio rate, seed, optimizer)
│   ├── hubert.yaml              # HuBERT SSL config
│   ├── wav2vec2.yaml            # Wav2Vec 2.0 config
│   ├── wavlm.yaml               # WavLM config
│   ├── emotion2vec_plus.yaml    # emotion2vec+ config
│   ├── beats.yaml               # BEATs spectrogram transformer config
│   ├── mfcc_cnn_bilstm.yaml     # 2D CNN + BiLSTM hybrid baseline config
│   ├── mfcc_lstm.yaml           # Recurrent baseline config
│   └── wav2vec2_xlsr_300m.yaml  # Multilingual XLS-R-300M config
│
├── preprocessing/               # Dataset standardizers (16 kHz mono 16-bit PCM)
│   ├── preprocess_ravdess.py    # RAVDESS extraction and actor-disjoint splits
│   ├── preprocess_cremad.py     # CREMA-D extraction and actor-disjoint splits
│   └── preprocess_multidataset.py
│
├── ser/                         # Modular Core Python Package
│   ├── core/                    # Registry, dynamic config loader, paths, seed determinism
│   ├── data/                    # Dataset loaders, dynamic collators & class weighting
│   ├── features/                # Acoustic signal extraction (MFCC, Delta, CMVN)
│   ├── models/                  # BaseSERModel, Transformer adapter, CNN-BiLSTM, LSTM
│   ├── training/                # Training loop (MPS/CUDA/CPU, AMP, Cosine LR, Early Stopping)
│   └── evaluation/              # Metrics (Acc, UAR, WAR, Macro-F1), reports & heatmaps
│
├── scripts/                     # CLI Entrypoints
│   ├── train.py                 # Train a single model on any dataset
│   ├── train_all.py             # Sequentially train all 8 models on any dataset
│   ├── evaluate.py              # Evaluate any trained checkpoint
│   ├── evaluate_ensemble.py     # Multi-model soft-voting ensemble
│   ├── compare_results.py       # Aggregate benchmark tables, rankings & curve plots
│   └── verify_metrics.py        # Comprehensive audit of all saved metrics and artifacts
│
├── outputs/                     # Benchmark Artifacts (Strictly Isolated by Dataset)
│   ├── ravdess/                 # All 8 models, checkpoints, ensemble & comparison
│   ├── cremad/                  # All 8 models, checkpoints, ensemble & comparison
│   └── savee/                   # All 8 models, checkpoints, ensemble & comparison
│
├── ravdess_preprocessed/        # Standardized 16 kHz RAVDESS dataset & metadata
├── cremad_preprocessed/         # Standardized 16 kHz CREMA-D dataset & metadata
├── savee_preprocessed/          # Standardized 16 kHz SAVEE dataset & metadata
└── tests/                       # Automated unit tests (pytest)
```

---

## 🚀 Setup & Installation

### 1. Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and set your Hugging Face access token:
```bash
cp .env.example .env
# Set HF_TOKEN in .env
```

---

## 🛠️ CLI Usage Guide

### Train a Single Model
Train any model by key. Outputs will automatically be placed in `outputs/<dataset>/<model>`:
```bash
# Train HuBERT on CREMA-D
python scripts/train.py --model hubert --data_dir cremad_preprocessed

# Train MFCC CNN-BiLSTM on RAVDESS
python scripts/train.py --model mfcc_cnn_bilstm --data_dir ravdess_preprocessed
```

### Train All 8 Models Sequentially
Run the full 8-model benchmark on a dataset:
```bash
python scripts/train_all.py --data_dir cremad_preprocessed --outputs_root outputs/cremad
```

### Evaluate Checkpoint on Unseen Speakers
```bash
python scripts/evaluate.py --model hubert --dataset cremad --checkpoint best
```

### Multi-Model Ensemble (Soft-Voting)
Fuse the prediction probabilities of top models on unseen test speakers:
```bash
# CREMA-D Ensemble (Top 5)
python scripts/evaluate_ensemble.py \
  --models hubert wav2vec2 emotion2vec_plus wavlm mfcc_cnn_bilstm \
  --weights 0.35 0.25 0.20 0.10 0.10 \
  --data_dir cremad_preprocessed \
  --outputs_root outputs/cremad \
  --split test

# RAVDESS Ensemble (Top 3)
python scripts/evaluate_ensemble.py \
  --models wavlm wav2vec2 mfcc_cnn_bilstm \
  --weights 0.50 0.30 0.20 \
  --data_dir ravdess_preprocessed \
  --outputs_root outputs/ravdess \
  --split test
```

### Compile Comparison Tables & Curves
Generate consolidated leaderboards, rankings, per-class F1 comparisons, and training curves:
```bash
# For CREMA-D
python scripts/compare_results.py --dataset cremad

# For RAVDESS
python scripts/compare_results.py --dataset ravdess
```

### Audit Metrics & Verify Pipeline
Validate that all files, training histories, confusion matrices, and metrics match expected formats:
```bash
python scripts/verify_metrics.py --dataset cremad
python scripts/verify_metrics.py --dataset ravdess

# Run unit tests
pytest tests/
```

---

## 🔬 Methodological Guarantees
1. **Zero Speaker Leakage**: Actors in the test partition never appear in training or validation splits.
2. **Dataset-Agnostic Core**: Emotion counts and classes are read dynamically from `metadata/labels.json` rather than hardcoded constants.
3. **Reproducibility**: Explicit random seeds are set across PyTorch, NumPy, and Python's random generator.
4. **Isolated Artifact Storage**: Checkpoints and metrics for each dataset are stored in completely separate subdirectories under `outputs/<dataset>/`.
