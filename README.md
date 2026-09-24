# Multi-Model & Multi-Corpus Speech Emotion Recognition (SER) Framework

A modular, production-grade PyTorch benchmarking framework for **Speech Emotion Recognition (SER)** across diverse speech corpora. Evaluates classical acoustic baselines against state-of-the-art self-supervised foundation models with strict speaker-independent and prompt-independent evaluation protocols (zero actor and zero prompt leakage).

---

## 📊 Comprehensive Benchmark Leaderboard

All evaluations are conducted strictly on **unseen actors or unseen prompts** (disjoint test partitions).

### 1. Universal Multi-Corpus Foundation Model (`outputs/combined/`)
*11,318 audio clips across 121 speakers unified into 6 canonical emotions (`neutral`, `happy`, `sad`, `angry`, `fear`, `disgust`).*  
*Evaluated on **1,701 strictly unseen clips** across all 4 datasets simultaneously. Random chance baseline: **16.67%**.*

| Architecture / Model | Training Strategy | Trainable Params | Test Accuracy | Macro-F1 | Test UAR | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Universal HuBERT** | **Transfer + Weighted Pooling (Frozen)** | **4,626** | **68.31%** | **0.6779** | **68.61%** | **🏆 Unified Champion (4.1× chance baseline)** |
| *Zero-Shot CREMA-D HuBERT* | Direct Evaluation (Zero-Shot) | 0 | 60.61% | 0.6031 | 60.54% | Baseline Multi-Corpus Benchmark |

#### Sub-Cohort Breakdown on Unseen Test Partitions:
| Sub-Cohort Dataset | Test Clips | Unseen Evaluation Property | Test Accuracy | Macro-F1 |
| :--- | :---: | :--- | :---: | :---: |
| **CREMA-D** | 1,060 | 13 Unseen Diverse Actors (IDs 1079–1091) | **72.45%** | **0.7232** |
| **TESS** | 360 | 30 Unseen Vocabulary Words (disjoint prompts) | **68.89%** | **0.6771** |
| **RAVDESS** | 176 | 4 Unseen Actors (Actors 21–24) | **52.27%** | **0.5018** |
| **SAVEE** | 105 | 1 Unseen British Actor (`KL`) | **51.43%** | **0.3999** |
| **OVERALL** | **1,701** | **Multi-Corpus Unseen Benchmark** | **68.31%** | **0.6779** |

---

### 2. CREMA-D Benchmark (91 Diverse Actors, 6 Emotion Classes)
*Evaluated on 1,060 test clips from 13 unseen actors (IDs 1079–1091). Random chance baseline: **16.67%**.*

| Rank | Model / Method | Architecture / Backbone | Test Accuracy | Macro-F1 | Test UAR | Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **🏆** | **Multi-Model Ensemble** | **Soft-Voting (Top 5)** | **75.57%** | **0.7594** | **75.61%** | **Peak Ensemble** |
| **🥇** | **HuBERT** | Acoustic Unit SSL (`facebook/hubert-base-ls960`) | **71.98%** | **0.7209** | **72.03%** | **#1 Single Model** |
| **🥈** | **Wav2Vec 2.0** | Contrastive SSL (`facebook/wav2vec2-base`) | **69.25%** | **0.6982** | **69.29%** | Strong Contrastive |
| **🥈** | **emotion2vec+** | Emotion-Specialized Pretrained | **69.25%** | **0.6982** | **69.29%** | Strong Acoustic SSL |
| **4** | **WavLM** | Denoising SSL (`microsoft/wavlm-base-plus`) | **66.32%** | **0.6584** | **66.45%** | Denoising SSL |
| **5** | **MFCC + CNN-BiLSTM** | 2D CNN Spectrogram + BiLSTM + Attention | **63.30%** | **0.6392** | **63.24%** | Best Classical Hybrid |
| **6** | **BEATs** | Acoustic Spectrogram Transformer | **62.64%** | **0.6190** | **62.89%** | Spectrogram Transformer |
| **7** | **MFCC + LSTM** | Sequential Baseline | **59.62%** | **0.5999** | **59.69%** | Recurrent Baseline |
| **8** | **Wav2Vec2-XLS-R-300M** | Multilingual Frozen Backbone | **24.43%** | **0.1346** | **23.85%** | Frozen Multilingual |

---

### 3. RAVDESS Benchmark (24 Actors, 8 Emotion Classes)
*Evaluated on 240 test clips from unseen Actors 21–24. Random chance baseline: **12.50%**.*

#### Enhanced / Transfer Learning Benchmark (`outputs/ravdess_enhanced/`):
| Rank | Model / Method | Backbone / Strategy | Test Accuracy | Macro-F1 | Test UAR | Improvement vs. Baseline |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **🏆** | **Transfer Ensemble (Top 3)** | **Soft-Voting (HuBERT + W2V2 + WavLM)** | **73.75%** | **0.7207** | **72.27%** | **+5.00% over Baseline Ensemble (68.75%)** |
| **🥇** | **HuBERT Transfer** | **CREMA-D $\rightarrow$ RAVDESS + Weighted Pooling** | **72.92%** | **0.7119** | **71.09%** | **+40.42% / 3.4× F1 over HuBERT scratch (32.50%)** |
| **🥈** | **Wav2Vec2 Transfer** | CREMA-D $\rightarrow$ RAVDESS + Weighted Pooling | **67.50%** | **0.6595** | **66.02%** | +17.50% over Wav2Vec2 scratch (50.00%) |
| **🥉** | **WavLM (Scratch Baseline)** | `microsoft/wavlm-base-plus` | **67.08%** | **0.6631** | **68.36%** | Baseline Single-Model Champion |
| **4** | **WavLM Transfer** | CREMA-D $\rightarrow$ RAVDESS + Weighted Pooling | **66.67%** | **0.6505** | **66.41%** | Denoising Transfer |

#### Full Baseline Benchmark (`outputs/ravdess/`):
| Model | Test Accuracy | Macro-F1 | Test UAR | Status |
| :--- | :---: | :---: | :---: | :--- |
| **Multi-Model Ensemble (Top 3)** | **68.75%** | **0.6791** | **68.75%** | Baseline Peak |
| **WavLM** | **67.08%** | **0.6631** | **67.08%** | Baseline #1 |
| **Wav2Vec 2.0** | **50.00%** | **0.4933** | **50.00%** | Baseline |
| **emotion2vec+** | **50.00%** | **0.4933** | **50.00%** | Baseline |
| **MFCC + CNN-BiLSTM** | **42.50%** | **0.3984** | **42.50%** | Baseline |
| **BEATs** | **34.58%** | **0.2466** | **34.58%** | Baseline |
| **MFCC + LSTM** | **32.92%** | **0.2817** | **32.92%** | Baseline |
| **HuBERT (Scratch)** | **32.50%** | **0.2117** | **32.50%** | Baseline |
| **Wav2Vec2-XLS-R-300M** | **13.33%** | **0.0294** | **12.50%** | Baseline |

---

### 4. SAVEE Benchmark (4 Actors, 7 Emotion Classes)
*Evaluated on 120 test clips from unseen British Actor `KL`. Random chance baseline: **14.29%**.*

| Model / Method | Strategy | Test Accuracy | Macro-F1 | Test UAR | Improvement |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Transfer Ensemble (Top 3)** | **Soft Voting (`outputs/savee_enhanced/ensemble/`)** | **51.67%** | **0.3860** | **40.48%** | **2.0× Accuracy / 5.8× F1 vs. Baseline** |
| **HuBERT Transfer** | **CREMA-D $\rightarrow$ SAVEE (Frozen Weighted Head)** | **45.83%** | **0.3419** | **38.10%** | **+20.00% / 4.3× F1 vs. Scratch (25.83%)** |
| *Baseline HuBERT (Scratch)* | Trained from scratch on 480 clips | 25.83% | 0.0795 | 15.24% | Overfitting Bottleneck |
| *Baseline Wav2Vec2 (Scratch)* | Trained from scratch on 480 clips | 25.83% | 0.2526 | 25.83% | Baseline |
| *Baseline emotion2vec+* | Trained from scratch on 480 clips | 25.83% | 0.2285 | 25.83% | Baseline |
| *Baseline WavLM (Scratch)* | Trained from scratch on 480 clips | 25.00% | 0.0649 | 14.29% | Overfitting Bottleneck |
| *Baseline Ensemble* | Soft-Voting across scratch models | 25.00% | 0.2312 | 25.00% | Baseline |
| *Baseline XLS-R-300M* | Frozen Multilingual | 18.33% | 0.1702 | 18.33% | Baseline |

---

### 5. TESS Benchmark (2 Female Actors, 7 Emotion Classes, 200 Words)
*Prompt-independent partition (zero word leakage on 30 unseen vocabulary words). Random baseline: **14.29%**.*

| Model / Method | Architecture / Backbone | Test Accuracy | Macro-F1 | Test UAR |
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

## 🌐 Cross-Corpus Generalization & Scientific Insights

### 1. Cross-Corpus Zero-Shot Generalization Matrix
*Evaluating models on target corpora with zero target training across the 6 shared canonical classes:*

| Source Model | Source Dataset | Target Dataset | Target Split | Zero-Shot Accuracy | Zero-Shot Macro-F1 | Zero-Shot UAR |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **HuBERT (CREMA-D)** | CREMA-D (64 spk) | **SAVEE** | Test (`KL`) | **52.38%** | **0.4163** | **44.44%** |
| **HuBERT Transfer** | RAVDESS (16 spk) | **CREMA-D** | Test (13 spk) | **53.68%** | **0.5270** | **53.80%** |
| **HuBERT Transfer** | RAVDESS (16 spk) | **TESS** | Test (Unseen words) | **45.95%** | **0.4025** | **45.95%** |
| **HuBERT Transfer** | RAVDESS (16 spk) | **SAVEE** | Test (`KL`) | **39.17%** | **0.2893** | **33.33%** |
| **HuBERT (CREMA-D)** | CREMA-D (64 spk) | **RAVDESS** | Test (Actors 21–24) | **40.34%** | **0.3363** | **38.02%** |
| **HuBERT (CREMA-D)** | CREMA-D (64 spk) | **TESS** | Test (Unseen words) | **38.89%** | **0.3221** | **38.89%** |

### 2. The Speaker Diversity Law
> **Key Finding**: The CREMA-D HuBERT model evaluated **zero-shot** on SAVEE achieves **52.38% Accuracy** and **0.4163 Macro-F1**, whereas training directly on SAVEE from scratch reached only **25.83% Accuracy** and **0.0795 Macro-F1**.  
> Exposure to diverse speakers (64 actors in CREMA-D) forces deep speech representations to isolate genuine emotion prosody rather than memorizing individual vocal tract characteristics.

### 3. Layer Weight Interpretability
Learned softmax weights across the 12 Transformer hidden states reveal that **emotional prosody concentrates in Layers 9–11 (~11.1% weight each)** rather than the final phonetic layer 12 (~9.2%) or early acoustic layers 1–3 (~7.1%).

---

## 📁 Repository Structure

```text
speech_emotion_detection-develop-v2/
├── configs/                     # Model architecture and training configs
│   ├── _base.yaml               # Shared defaults (sample rate, seed, optimizer)
│   ├── hubert.yaml              # HuBERT SSL configuration
│   ├── wav2vec2.yaml            # Wav2Vec 2.0 configuration
│   ├── wavlm.yaml               # WavLM configuration
│   ├── emotion2vec_plus.yaml    # emotion2vec+ configuration
│   ├── beats.yaml               # BEATs spectrogram transformer configuration
│   ├── mfcc_cnn_bilstm.yaml     # 2D CNN + BiLSTM hybrid baseline configuration
│   ├── mfcc_lstm.yaml           # Recurrent baseline configuration
│   └── wav2vec2_xlsr_300m.yaml  # Multilingual XLS-R-300M configuration
│
├── preprocessing/               # Standardized 16 kHz Mono 16-bit PCM Ingestion
│   ├── preprocess_ravdess.py    # RAVDESS extraction (actor-disjoint splits)
│   ├── preprocess_cremad.py     # CREMA-D extraction (actor-disjoint splits)
│   ├── preprocess_savee.py      # SAVEE extraction (actor-disjoint splits)
│   ├── preprocess_tess.py       # TESS extraction (word-disjoint prompt splits)
│   ├── preprocess_combined.py   # Multi-corpus 4-dataset zero-leakage unifier
│   └── preprocess_multidataset.py
│
├── ser/                         # Modular Core Python Framework
│   ├── core/                    # Registry, config loader, paths, seed determinism
│   ├── data/                    # Dataset loaders, dynamic collators & class weighting
│   ├── features/                # Acoustic signal extraction (MFCC, Delta, CMVN)
│   ├── models/                  # BaseSERModel, Transformer with Layer Pooling, CNN-BiLSTM, LSTM
│   ├── training/                # Training engine (MPS/CUDA/CPU, AMP, Cosine Annealing, Early Stopping)
│   └── evaluation/              # Metrics (Acc, UAR, WAR, Macro-F1), reports & heatmaps
│
├── scripts/                     # Command-Line Interfaces
│   ├── train.py                 # Train a single model on any dataset from scratch
│   ├── train_all.py             # Sequentially train all 8 models on any dataset
│   ├── train_transfer.py        # Fine-tune pre-trained models with weighted layer pooling
│   ├── evaluate.py              # Evaluate any checkpoint on in-domain test splits
│   ├── evaluate_ensemble.py     # Multi-model soft-voting ensemble
│   ├── evaluate_cross_corpus.py # Cross-corpus zero-shot evaluation pipeline
│   ├── compare_results.py       # Aggregate benchmark tables, rankings & curve plots
│   ├── verify_metrics.py        # Comprehensive verification of metrics and artifacts
│   ├── verify_training.py       # Sanity check for forward/backward passes
│   └── verify_all.py            # End-to-end pipeline auditor
│
├── tests/                       # Automated Test Suite (pytest)
│   ├── conftest.py              # Synthetic audio and mock dataset fixtures
│   ├── test_combined.py         # Multi-corpus zero-leakage and symlink tests
│   ├── test_cross_corpus.py     # Cross-corpus label alignment tests
│   ├── test_labels.py           # Canonical label mapper verification
│   ├── test_pooling.py          # Weighted layer pooling tensor operations
│   └── test_split.py            # Disjoint speaker/prompt split guard tests
│
├── outputs/                     # Benchmark Artifacts (Strictly Isolated by Dataset)
│   ├── combined/                # Universal multi-corpus foundation model artifacts
│   ├── cross_corpus/            # Zero-shot cross-corpus evaluation matrices
│   ├── cremad/                  # CREMA-D models, checkpoints, ensembles & plots
│   ├── ravdess/                 # RAVDESS baseline models, ensembles & plots
│   ├── ravdess_enhanced/        # RAVDESS transfer models & peak ensemble
│   ├── savee/                   # SAVEE baseline models & plots
│   ├── savee_enhanced/          # SAVEE transfer models & peak ensemble
│   └── tess/                    # TESS models, ensembles & plots
│
├── PROJECT_OVERVIEW.md          # Comprehensive research dashboard and logs
├── pyproject.toml               # Package build configuration & metadata
├── requirements.txt             # Primary Python dependencies
└── .gitignore                   # Comprehensive ignore rules for ML/audio artifacts
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

### 1. Preprocess Datasets
Standardize raw audio into 16 kHz mono 16-bit PCM with verified disjoint splits:
```bash
# CREMA-D
python preprocessing/preprocess_cremad.py

# RAVDESS
python preprocessing/preprocess_ravdess.py

# SAVEE
python preprocessing/preprocess_savee.py

# TESS
python preprocessing/preprocess_tess.py

# Universal Multi-Corpus Combined Dataset
python preprocessing/preprocess_combined.py
```

### 2. Train a Single Model from Scratch
```bash
# Train HuBERT on CREMA-D
python scripts/train.py --model hubert --data_dir cremad_preprocessed

# Train MFCC CNN-BiLSTM on RAVDESS
python scripts/train.py --model mfcc_cnn_bilstm --data_dir ravdess_preprocessed
```

### 3. Transfer Learning with Weighted Layer Pooling
Transfer knowledge from CREMA-D to smaller datasets using learned layer pooling:
```bash
# Fine-tune HuBERT on RAVDESS with Weighted Layer Pooling
python scripts/train_transfer.py \
  --checkpoint outputs/cremad/hubert/checkpoints/best_model.pt \
  --data_dir ravdess_preprocessed \
  --output_dir outputs/ravdess_enhanced/hubert_transfer_cremad_weighted \
  --pooling weighted \
  --epochs 20 \
  --lr 1e-4

# Fine-tune HuBERT on SAVEE with Frozen Backbone
python scripts/train_transfer.py \
  --checkpoint outputs/cremad/hubert/checkpoints/best_model.pt \
  --data_dir savee_preprocessed \
  --output_dir outputs/savee_enhanced/hubert_transfer_cremad_weighted_frozen \
  --pooling weighted \
  --freeze_encoder \
  --epochs 25 \
  --lr 5e-4
```

### 4. Multi-Model Soft-Voting Ensemble
```bash
# CREMA-D Top-5 Ensemble
python scripts/evaluate_ensemble.py \
  --models hubert wav2vec2 emotion2vec_plus wavlm mfcc_cnn_bilstm \
  --weights 0.35 0.25 0.20 0.10 0.10 \
  --data_dir cremad_preprocessed \
  --outputs_root outputs/cremad \
  --split test

# RAVDESS Enhanced Transfer Ensemble
python scripts/evaluate_ensemble.py \
  --models hubert_transfer_cremad_weighted wav2vec2_transfer_cremad_weighted wavlm_transfer_cremad_weighted \
  --weights 0.45 0.35 0.20 \
  --data_dir ravdess_preprocessed \
  --outputs_root outputs/ravdess_enhanced \
  --split test
```

### 5. Cross-Corpus Zero-Shot Evaluation
Evaluate a trained model directly on an unseen target dataset across canonical emotion classes:
```bash
python scripts/evaluate_cross_corpus.py \
  --checkpoint outputs/cremad/hubert/checkpoints/best_model.pt \
  --source_dataset cremad \
  --target_dataset savee \
  --data_dir savee_preprocessed \
  --output_dir outputs/cross_corpus/cremad_hubert/to_savee
```

### 6. Run Unit Tests & Audit Metrics
```bash
# Run complete test suite (15 unit tests)
pytest tests/

# Audit saved metrics and training artifacts
python scripts/verify_metrics.py --dataset cremad
python scripts/verify_metrics.py --dataset ravdess
python scripts/verify_metrics.py --dataset savee
python scripts/verify_metrics.py --dataset tess
```

---

## 🔬 Methodological Guarantees

1. **Strict Zero-Leakage Partitions**:
   - **Speaker-Independent**: Test partitions for CREMA-D, RAVDESS, and SAVEE feature actors who never appear in training or validation splits.
   - **Prompt-Independent**: Test partitions for TESS feature 30 vocabulary words never spoken in the training split.
2. **Dynamic Label Discovery**:
   - Class indices, labels, and class counts are discovered dynamically at runtime via `metadata/labels.json` and canonical mappers.
3. **Reproducibility**:
   - Deterministic seeds are enforced across PyTorch, NumPy, and Python's random library.
4. **Isolated Artifact Namespaces**:
   - Checkpoints, curves, and confusion matrices for each dataset and experiment are isolated under `outputs/<dataset>/`.
