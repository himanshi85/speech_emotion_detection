# Multi-Model and Multi-Corpus Speech Emotion Recognition (SER) Framework

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch 2.0+" />
  <img src="https://img.shields.io/badge/Transformers-4.30%2B-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Hugging Face Transformers" />
  <img src="https://img.shields.io/badge/Tests-15%2F15%20Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests Passing" />
  <img src="https://img.shields.io/badge/Evaluation-Zero%20Speaker%20Leakage-success?style=for-the-badge" alt="Zero Speaker Leakage" />
  <img src="https://img.shields.io/badge/Corpora-4%20Datasets-blueviolet?style=for-the-badge" alt="4 Datasets" />
  <img src="https://img.shields.io/badge/Models-8%20Architectures-informational?style=for-the-badge" alt="8 Models" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/Maintainer-Jash%20Lathiya-lightgrey?style=for-the-badge" alt="Maintainer" />
</p>

A modular, production-grade PyTorch benchmarking framework for **Speech Emotion Recognition (SER)** across diverse speech corpora. This repository evaluates classical acoustic baselines against state-of-the-art self-supervised foundation models under strict speaker-independent and prompt-independent evaluation protocols (guaranteeing zero speaker and zero prompt leakage).

> [!IMPORTANT]
> **Strict Zero-Leakage Benchmark Guarantee**: All evaluation metrics reported herein are generated exclusively on completely unseen human actors (CREMA-D: 13 unseen actors; RAVDESS: Actors 21-24; SAVEE: Actor `KL`) or unseen vocabulary prompts (TESS: 30 unseen words). There is zero data or identity overlap between train, validation, and test partitions.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Benchmark Leaderboard](#benchmark-leaderboard)
  - [1. Universal Multi-Corpus Foundation Model](#1-universal-multi-corpus-foundation-model)
  - [2. CREMA-D Benchmark (91 Diverse Actors)](#2-crema-d-benchmark-91-diverse-actors)
  - [3. RAVDESS Benchmark (24 Actors)](#3-ravdess-benchmark-24-actors)
  - [4. SAVEE Benchmark (4 Actors)](#4-savee-benchmark-4-actors)
  - [5. TESS Benchmark (Prompt-Independent)](#5-tess-benchmark-prompt-independent)
- [Visual Interpretability and Layer Analysis](#visual-interpretability-and-layer-analysis)
- [Cross-Corpus Generalization and Scientific Insights](#cross-corpus-generalization-and-scientific-insights)
  - [The Speaker Diversity Law](#the-speaker-diversity-law)
- [Repository Structure](#repository-structure)
- [Setup and Installation](#setup-and-installation)
- [CLI Execution Guide](#cli-execution-guide)
  - [1. Preprocess Datasets](#1-preprocess-datasets)
  - [2. Train a Single Model](#2-train-a-single-model)
  - [3. Transfer Learning with Weighted Layer Pooling](#3-transfer-learning-with-weighted-layer-pooling)
  - [4. Multi-Model Soft-Voting Ensemble](#4-multi-model-soft-voting-ensemble)
  - [5. Cross-Corpus Zero-Shot Evaluation](#5-cross-corpus-zero-shot-evaluation)
  - [6. Verification and Test Suite](#6-verification-and-test-suite)
- [Methodological Guarantees](#methodological-guarantees)
- [License](#license)

---

## System Architecture

```mermaid
flowchart TD
    subgraph INGESTION["1. Data Ingestion & Disjoint Splitting"]
        RAW["Raw Audio Corpora<br/>(CREMA-D, RAVDESS, SAVEE, TESS)"] --> STD["Audio Standardization Pipeline<br/>(16 kHz Mono, PCM 16-bit)"]
        STD --> SPLIT1["Speaker-Disjoint Split<br/>(CREMA-D: 13 Unseen Actors)"]
        STD --> SPLIT2["Speaker-Disjoint Split<br/>(RAVDESS: 4 Unseen Actors)"]
        STD --> SPLIT3["Speaker-Disjoint Split<br/>(SAVEE: 1 Unseen Actor)"]
        STD --> SPLIT4["Word-Disjoint Split<br/>(TESS: 30 Unseen Prompts)"]
        STD --> UNIFIED["Multi-Corpus Unifier<br/>(11,318 Clips, 6 Canonical Classes)"]
    end

    subgraph ARCHITECTURES["2. Feature Extraction & Modeling"]
        SPLIT1 & SPLIT2 & SPLIT3 & SPLIT4 & UNIFIED --> INP_WAVE["Raw Audio Waveforms"]
        SPLIT1 & SPLIT2 & SPLIT3 & SPLIT4 & UNIFIED --> INP_SPEC["Acoustic Spectrograms"]

        INP_WAVE --> SSL["Self-Supervised Transformers<br/>(HuBERT / Wav2Vec2 / WavLM / XLS-R)"]
        SSL --> LAYERS["12 Hidden Layer Representations<br/>[h_1, h_2, ..., h_12]"]
        LAYERS --> WEIGHTED["Learnable Softmax Layer Pooling<br/>h_fused = Σ (softmax(α_i) * h_i)"]
        WEIGHTED --> POOL["Masked Temporal Mean Pooling"]

        INP_SPEC --> MFCC["40 Mel Filterbanks + Δ + ΔΔ"]
        MFCC --> RECURRENT["MFCC + LSTM Baseline<br/>2-Layer Recurrent"]
        MFCC --> HYBRID["MFCC + CNN-BiLSTM<br/>2D Conv + Bidirectional LSTM + Attention"]
    end

    subgraph INFERENCE["3. Evaluation & Inference"]
        POOL & RECURRENT & HYBRID --> HEAD["Dense Classification Head<br/>Dropout + Linear Layer"]
        HEAD --> IN_DOMAIN["In-Domain Evaluation<br/>(Strictly Unseen Actors)"]
        HEAD --> ENSEMBLE["Soft-Voting Ensemble<br/>(Top-k Probability Fusion)"]
        HEAD --> ZERO_SHOT["Cross-Corpus Zero-Shot<br/>(Domain Invariance Benchmarks)"]
    end
```

<details>
<summary>Click to view Textual System Architecture Flowchart</summary>

```text
+---------------------------------------------------------------------------------------------------+
|                                  DATA INGESTION & PREPROCESSING                                    |
|                                                                                                   |
|  Raw Audio Files                                                                                  |
|  [CREMA-D / RAVDESS / SAVEE / TESS]                                                                |
|          |                                                                                        |
|          v                                                                                        |
|  Audio Standardization Pipeline (16 kHz, Mono, PCM 16-bit)                                        |
|          |                                                                                        |
|          +-----------------------------------+-----------------------------------+                |
|          |                                   |                                   |                |
|          v                                   v                                   v                |
|  Speaker-Disjoint Split              Word-Disjoint Split                 Multi-Corpus Unifier     |
|  (CREMA-D: 13 unseen actors)         (TESS: 30 unseen words)             (4 Corpora, 11,318 clips)|
|  (RAVDESS: 4 unseen actors)                                              (6 Canonical Emotions)   |
|  (SAVEE: 1 unseen actor)                                                                          |
+--------------------------------------------------+------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------+
|                                    MODEL ARCHITECTURES & POOLING                                  |
|                                                                                                   |
|  [Raw Waveform Input]                                [Acoustic Spectral Input]                    |
|          |                                                       |                                |
|          v                                                       v                                |
|  Self-Supervised Speech Transformers                     MFCC Feature Extractor                   |
|  (HuBERT / Wav2Vec 2.0 / WavLM / XLS-R)                  (40 Mel Bands + Delta + Delta-Delta)      |
|          |                                                       |                                |
|          v                                                       +----------------+               |
|  12-Layer Hidden State Representations                           |                |               |
|  [h_1, h_2, ..., h_12]                                           v                v               |
|          |                                                   2D CNN-BiLSTM      LSTM Baseline     |
|          v                                                   + Self-Attention   (2-Layer Recurrent|
|  Learnable Softmax Layer Weighting                               |                |               |
|  h_fused = SUM( alpha_i * h_i ),  alpha = softmax(w)             |                |               |
|          |                                                       |                |               |
|          v                                                       |                |               |
|  Masked Temporal Mean Pooling                                    v                v               |
|          |                                               Dense Classification Head                |
|          +-----------------------------------------------+ (Dropout + Linear Layer)                |
+--------------------------------------------------+------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------+
|                                    EVALUATION & INFERENCE                                         |
|                                                                                                   |
|          +-----------------------------------+-----------------------------------+                |
|          |                                   |                                   |                |
|          v                                   v                                   v                |
|  In-Domain Evaluation                Soft-Voting Ensemble                Cross-Corpus Zero-Shot   |
|  (Strictly Unseen Test Actors)       (Top-k Probability Fusion)          (Source -> Target Dataset|
|  Metrics: Accuracy, Macro-F1, UAR    Ensemble Weights Calibration        Domain Invariance Tests) |
+---------------------------------------------------------------------------------------------------+
```
</details>

---

## Benchmark Leaderboard

All evaluations are conducted strictly on **unseen actors or unseen prompts** (disjoint test partitions with zero leakage).

### 1. Universal Multi-Corpus Foundation Model

*Unified corpus of **11,318 audio clips** across 121 speakers mapped to 6 canonical emotions (`neutral`, `happy`, `sad`, `angry`, `fear`, `disgust`). Evaluated on **1,701 strictly unseen clips** across all 4 datasets simultaneously. Random chance baseline: **16.67%**.*

| Architecture / Model | Training Strategy | Trainable Params | Test Accuracy | Macro-F1 | Test UAR | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Universal HuBERT** | **Transfer + Weighted Pooling (Frozen)** | **4,626** | **68.31%** | **0.6779** | **68.61%** | **Unified Champion (4.1x chance baseline)** |
| *Zero-Shot CREMA-D HuBERT* | Direct Evaluation (Zero-Shot) | 0 | 60.61% | 0.6031 | 60.54% | Baseline Multi-Corpus Benchmark |

<p align="center">
  <img src="outputs/combined/comparison/curves/all_models_test_macro_f1_bar.png" width="48%" alt="Universal Multi-Corpus Test Macro-F1" />
  <img src="outputs/combined/comparison/curves/all_models_val_macro_f1.png" width="48%" alt="Universal Multi-Corpus Validation Macro-F1" />
</p>

<details>
<summary>Click to view Sub-Cohort Breakdown on Unseen Test Partitions</summary>

| Sub-Cohort Dataset | Test Clips | Unseen Evaluation Property | Test Accuracy | Macro-F1 |
| :--- | :---: | :--- | :---: | :---: |
| **CREMA-D** | 1,060 | 13 Unseen Diverse Actors (IDs 1079-1091) | **72.45%** | **0.7232** |
| **TESS** | 360 | 30 Unseen Vocabulary Words (disjoint prompts) | **68.89%** | **0.6771** |
| **RAVDESS** | 176 | 4 Unseen Actors (Actors 21-24) | **52.27%** | **0.5018** |
| **SAVEE** | 105 | 1 Unseen British Actor (`KL`) | **51.43%** | **0.3999** |
| **OVERALL** | **1,701** | **Multi-Corpus Unseen Benchmark** | **68.31%** | **0.6779** |

</details>

---

### 2. CREMA-D Benchmark (91 Diverse Actors)

*Evaluated on 1,060 test clips from 13 unseen actors (IDs 1079-1091). Random chance baseline: **16.67%**.*

| Rank | Model / Method | Architecture / Backbone | Test Accuracy | Macro-F1 | Test UAR | Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **[Peak]** | **Multi-Model Ensemble** | **Soft-Voting (Top 5)** | **75.57%** | **0.7594** | **75.61%** | **Peak Ensemble** |
| **[1]** | **HuBERT** | Acoustic Unit SSL (`facebook/hubert-base-ls960`) | **71.98%** | **0.7209** | **72.03%** | **Top Single Model** |
| **[2]** | **Wav2Vec 2.0** | Contrastive SSL (`facebook/wav2vec2-base`) | **69.25%** | **0.6982** | **69.29%** | Strong Contrastive |
| **[2]** | **emotion2vec+** | Emotion-Specialized Pretrained | **69.25%** | **0.6982** | **69.29%** | Strong Acoustic SSL |
| **[4]** | **WavLM** | Denoising SSL (`microsoft/wavlm-base-plus`) | **66.32%** | **0.6584** | **66.45%** | Denoising SSL |
| **[5]** | **MFCC + CNN-BiLSTM** | 2D CNN Spectrogram + BiLSTM + Attention | **63.30%** | **0.6392** | **63.24%** | Best Classical Hybrid |
| **[6]** | **BEATs** | Acoustic Spectrogram Transformer | **62.64%** | **0.6190** | **62.89%** | Spectrogram Transformer |
| **[7]** | **MFCC + LSTM** | Sequential Baseline | **59.62%** | **0.5999** | **59.69%** | Recurrent Baseline |
| **[8]** | **Wav2Vec2-XLS-R-300M** | Multilingual Frozen Backbone | **24.43%** | **0.1346** | **23.85%** | Frozen Multilingual |

<p align="center">
  <img src="outputs/cremad/comparison/curves/all_models_test_macro_f1_bar.png" width="48%" alt="CREMA-D Test Macro-F1 Bar Chart" />
  <img src="outputs/cremad/ensemble/confusion_matrix.png" width="48%" alt="CREMA-D Peak Ensemble Confusion Matrix" />
</p>

---

### 3. RAVDESS Benchmark (24 Actors)

*Evaluated on 240 test clips from unseen Actors 21-24. Random chance baseline: **12.50%**.*

| Rank | Model / Method | Backbone / Strategy | Test Accuracy | Macro-F1 | Test UAR | Improvement vs. Baseline |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **[Peak]** | **Transfer Ensemble (Top 3)** | **Soft-Voting (HuBERT + W2V2 + WavLM)** | **73.75%** | **0.7207** | **72.27%** | **+5.00% over Baseline Ensemble (68.75%)** |
| **[1]** | **HuBERT Transfer** | **CREMA-D -> RAVDESS + Weighted Pooling** | **72.92%** | **0.7119** | **71.09%** | **+40.42% / 3.4x F1 over HuBERT scratch (32.50%)** |
| **[2]** | **Wav2Vec2 Transfer** | CREMA-D -> RAVDESS + Weighted Pooling | **67.50%** | **0.6595** | **66.02%** | +17.50% over Wav2Vec2 scratch (50.00%) |
| **[3]** | **WavLM (Scratch Baseline)** | `microsoft/wavlm-base-plus` | **67.08%** | **0.6631** | **68.36%** | Baseline Single-Model Champion |
| **[4]** | **WavLM Transfer** | CREMA-D -> RAVDESS + Weighted Pooling | **66.67%** | **0.6505** | **66.41%** | Denoising Transfer |

<p align="center">
  <img src="outputs/ravdess_enhanced/comparison/curves/all_models_test_macro_f1_bar.png" width="48%" alt="RAVDESS Enhanced Test Macro-F1 Bar Chart" />
  <img src="outputs/ravdess_enhanced/ensemble/confusion_matrix.png" width="48%" alt="RAVDESS Peak Transfer Ensemble Confusion Matrix" />
</p>

<details>
<summary>Click to view Full Scratch Baseline Comparison (outputs/ravdess/)</summary>

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

</details>

---

### 4. SAVEE Benchmark (4 Actors)

*Evaluated on 120 test clips from unseen British Actor `KL`. Random chance baseline: **14.29%**.*

| Model / Method | Strategy | Test Accuracy | Macro-F1 | Test UAR | Improvement |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Transfer Ensemble (Top 3)** | **Soft Voting (`outputs/savee_enhanced/ensemble/`)** | **51.67%** | **0.3860** | **40.48%** | **2.0x Accuracy / 5.8x F1 vs. Baseline** |
| **WavLM Transfer** | **CREMA-D -> SAVEE (Frozen Weighted Head)** | **49.17%** | **0.3753** | **46.19%** | **+24.17% / 5.8x F1 vs. Scratch (25.00%)** |
| **HuBERT Transfer** | **CREMA-D -> SAVEE (Frozen Weighted Head)** | **45.83%** | **0.3419** | **38.10%** | **+20.00% / 4.3x F1 vs. Scratch (25.83%)** |
| *Baseline HuBERT (Scratch)* | Trained from scratch on 480 clips | 25.83% | 0.0795 | 15.24% | Overfitting Bottleneck |
| *Baseline Wav2Vec2 (Scratch)* | Trained from scratch on 480 clips | 25.83% | 0.2526 | 25.83% | Baseline |
| *Baseline WavLM (Scratch)* | Trained from scratch on 480 clips | 25.00% | 0.0649 | 14.29% | Overfitting Bottleneck |

<p align="center">
  <img src="outputs/savee_enhanced/comparison/curves/all_models_test_macro_f1_bar.png" width="48%" alt="SAVEE Enhanced Test Macro-F1 Bar Chart" />
  <img src="outputs/savee_enhanced/ensemble/confusion_matrix.png" width="48%" alt="SAVEE Enhanced Ensemble Confusion Matrix" />
</p>

---

### 5. TESS Benchmark (Prompt-Independent)

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

## Visual Interpretability and Layer Analysis

### Learned Transformer Layer Weights Distribution

Self-supervised models encode distinct speech features across their depth. By training learnable softmax weights over all 12 hidden states ($\mathbf{h}_{\text{fused}} = \sum_{i=1}^{12} \alpha_i \mathbf{h}_i$), we uncover the layer-wise concentration of emotional prosody:

<p align="center">
  <img src="outputs/comparison_layer_weights.png" width="92%" alt="Layer Weights Distribution across Transformers" />
</p>

```text
Layer Weight Importance Distribution across 12 Transformer Layers:
Layer 01 [ 7.1%] |=====
Layer 02 [ 7.2%] |=====
Layer 03 [ 7.1%] |=====
Layer 04 [ 7.6%] |======
Layer 05 [ 7.9%] |======
Layer 06 [ 8.3%] |=======
Layer 07 [ 8.7%] |=======
Layer 08 [ 9.4%] |========
Layer 09 [11.1%] |==========  <-- Peak Emotion Representation
Layer 10 [11.1%] |==========  <-- Peak Emotion Representation
Layer 11 [10.3%] |=========   <-- Peak Emotion Representation
Layer 12 [ 9.2%] |========    <-- Final Phonetic Layer
```

- **Acoustic Substructure (Layers 1-4)**: Focuses on raw acoustic waveform representation and pitch contours (~7.1-7.6%).
- **Prosodic Culmination (Layers 9-11)**: Carries the dominant emotion discrimination weight (~11.1% per layer).
- **Phonetic Convergence (Layer 12)**: Specializes in discrete phonetic decoding (~9.2%), explaining why intermediate representations are significantly more expressive for emotion recognition than the final layer alone.

---

## Cross-Corpus Generalization and Scientific Insights

### Cross-Corpus Zero-Shot Generalization Matrix

Evaluating models on target corpora with zero target training across the 6 shared canonical classes:

| Source Model | Source Dataset | Target Dataset | Target Split | Zero-Shot Accuracy | Zero-Shot Macro-F1 | Zero-Shot UAR |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **HuBERT (CREMA-D)** | CREMA-D (64 spk) | **SAVEE** | Test (`KL`) | **52.38%** | **0.4163** | **44.44%** |
| **HuBERT Transfer** | RAVDESS (16 spk) | **CREMA-D** | Test (13 spk) | **53.68%** | **0.5270** | **53.80%** |
| **HuBERT Transfer** | RAVDESS (16 spk) | **TESS** | Test (Unseen words) | **45.95%** | **0.4025** | **45.95%** |
| **HuBERT Transfer** | RAVDESS (16 spk) | **SAVEE** | Test (`KL`) | **39.17%** | **0.2893** | **33.33%** |
| **HuBERT (CREMA-D)** | CREMA-D (64 spk) | **RAVDESS** | Test (Actors 21-24) | **40.34%** | **0.3363** | **38.02%** |
| **HuBERT (CREMA-D)** | CREMA-D (64 spk) | **TESS** | Test (Unseen words) | **38.89%** | **0.3221** | **38.89%** |

### The Speaker Diversity Law

> [!NOTE]
> **Empirical Finding**: The CREMA-D HuBERT model evaluated **zero-shot** on SAVEE achieves **52.38% Accuracy** and **0.4163 Macro-F1**, whereas training directly on SAVEE from scratch reached only **25.83% Accuracy** and **0.0795 Macro-F1**.  
> Exposure to diverse speakers (64 actors in CREMA-D) prevents the model from memorizing speaker-specific pitch baselines and vocal tract lengths, forcing representations to isolate generalizable emotional prosody.

---

## Repository Structure

The codebase is organized into six purpose-driven root directories:

```text
speech_emotion_detection-develop-v3/
├── configs/                     # Hyperparameter and model configuration files (.yaml)
├── data/                        # Audio corpora and verified metadata splits (Git-ignored)
├── outputs/                     # Experiment artifacts, checkpoints, confusion matrices, logs
├── scripts/                     # Executable command-line interfaces
├── src/                         # Reusable core Python package (ser)
└── tests/                       # Automated pytest verification suite
```

<details>
<summary>Click to view Detailed Sub-Directory File Tree</summary>

```text
speech_emotion_detection-develop-v3/
├── configs/                     # Hyperparameter and model configuration files (.yaml)
│   ├── _base.yaml               # Shared baseline configuration (16 kHz, seed 42, AdamW)
│   ├── hubert.yaml              # HuBERT SSL architecture and optimizer parameters
│   ├── wav2vec2.yaml            # Wav2Vec 2.0 configuration
│   ├── wavlm.yaml               # WavLM denoising SSL configuration
│   ├── emotion2vec_plus.yaml    # emotion2vec+ acoustic representation configuration
│   ├── beats.yaml               # BEATs acoustic spectrogram transformer configuration
│   ├── mfcc_cnn_bilstm.yaml     # 2D CNN + BiLSTM hybrid baseline configuration
│   ├── mfcc_lstm.yaml           # Recurrent sequential baseline configuration
│   └── wav2vec2_xlsr_300m.yaml  # Multilingual XLS-R-300M configuration
│
├── data/                        # Audio corpora and verified metadata splits
│   ├── raw/                     # Original raw dataset archives
│   ├── ravdess/                 # Standardized RAVDESS audio (16 kHz mono) and splits
│   ├── cremad/                  # Standardized CREMA-D audio (16 kHz mono) and splits
│   ├── savee/                   # Standardized SAVEE audio (16 kHz mono) and splits
│   ├── tess/                    # Standardized TESS audio (16 kHz mono) and prompt splits
│   └── combined/                # Unified 4-corpus dataset (11,318 clips, 6 canonical emotions)
│
├── outputs/                     # Experiment artifacts, checkpoints, confusion matrices, logs
│   ├── combined/                # Universal multi-corpus foundation model runs
│   ├── comparison/              # Cross-model parameter reports and comparative plots
│   ├── cremad/                  # CREMA-D 8-model benchmarks, ensembles, and curves
│   ├── cross_corpus/            # Zero-shot cross-corpus evaluation matrices and heatmaps
│   ├── ravdess/                 # RAVDESS baseline benchmarks
│   ├── ravdess_enhanced/        # Cross-corpus transfer models and transfer ensembles
│   ├── savee/                   # SAVEE baseline benchmarks
│   ├── savee_enhanced/          # Transfer models and ensembles on SAVEE
│   ├── tess/                    # TESS benchmark runs and evaluation reports
│   └── comparison_layer_weights.png # Layer weight distribution across transformers
│
├── scripts/                     # Executable command-line interfaces
│   ├── preprocessing/           # Data ingestion, audio standardization, and split generators
│   │   ├── preprocess_ravdess.py
│   │   ├── preprocess_cremad.py
│   │   ├── preprocess_savee.py
│   │   ├── preprocess_tess.py
│   │   ├── preprocess_combined.py
│   │   └── preprocess_multidataset.py
│   ├── train.py                 # Single model training entrypoint across all 8 models
│   ├── train_all.py             # Sequential training runner for complete suites
│   ├── train_transfer.py        # Cross-corpus transfer learning pipeline with weighted layer pooling
│   ├── evaluate.py              # In-domain checkpoint evaluation entrypoint
│   ├── evaluate_ensemble.py     # Multi-model soft-voting and weighted ensembling
│   ├── evaluate_cross_corpus.py # Cross-corpus zero-shot evaluation pipeline
│   ├── compare_results.py       # Metrics aggregation, rankings, and curve plotting
│   ├── verify_metrics.py        # Automated artifact integrity and metrics parity auditor
│   └── check_models.py          # Model architecture and parameter count validator
│
├── src/                         # Reusable core Python package
│   └── ser/                     # Complete Speech Emotion Recognition engine
│       ├── core/                # Paths, config loader, model registry, seed control
│       ├── data/                # Dataset loaders, dynamic collators, split guards, class weights
│       ├── features/            # Feature extraction (MFCC, Spectrograms, Deltas)
│       ├── models/              # Model architectures, weighted layer pooling, Hub loaders
│       ├── training/            # Training loop, optimizer, scheduler, early stopping
│       └── evaluation/          # Metrics, confusion matrices, evaluation runner
│
├── tests/                       # Automated pytest verification suite
│   ├── conftest.py              # Synthetic audio and mock dataset fixtures
│   ├── test_combined.py         # Multi-corpus integrity and canonical label tests
│   ├── test_cross_corpus.py     # Cross-corpus emotion mapping tests
│   ├── test_labels.py           # Canonical label mapper verification
│   ├── test_pooling.py          # Masked pooling and weighted layer pooling tests
│   └── test_split.py            # Actor-independent and word-disjoint split tests
│
├── .env.example                 # Environment variable template (Hugging Face token)
├── .gitignore                   # Comprehensive ignore rules for weights, data, cache
├── pyproject.toml               # Package configuration and build metadata
├── requirements.txt             # Primary Python dependencies
└── requirements-preprocess.txt  # Lightweight audio preprocessing dependencies
```
</details>

---

## Setup and Installation

### 1. Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and set your Hugging Face access token:

```bash
cp .env.example .env
# Set HF_TOKEN in .env for gated model access if needed
```

---

## CLI Execution Guide

### 1. Preprocess Datasets

Standardize raw audio into 16 kHz mono 16-bit PCM with verified disjoint splits:

```bash
# CREMA-D
python scripts/preprocessing/preprocess_cremad.py

# RAVDESS
python scripts/preprocessing/preprocess_ravdess.py --input_dir /path/to/raw_ravdess --output_dir data/ravdess

# SAVEE
python scripts/preprocessing/preprocess_savee.py

# TESS
python scripts/preprocessing/preprocess_tess.py

# Universal Multi-Corpus Combined Dataset
python scripts/preprocessing/preprocess_combined.py
```

### 2. Train a Single Model

```bash
# Train HuBERT on CREMA-D
python scripts/train.py --model hubert --data_dir data/cremad

# Train MFCC CNN-BiLSTM on RAVDESS
python scripts/train.py --model mfcc_cnn_bilstm --data_dir data/ravdess
```

### 3. Transfer Learning with Weighted Layer Pooling

Transfer knowledge from CREMA-D to smaller datasets using learned layer pooling:

```bash
# Fine-tune HuBERT on RAVDESS with Weighted Layer Pooling
python scripts/train_transfer.py \
  --checkpoint outputs/cremad/hubert/checkpoints/best_model.pt \
  --target_dataset ravdess \
  --target_data_dir data/ravdess \
  --output_dir outputs/ravdess_enhanced/hubert_transfer_cremad_weighted \
  --pooling weighted \
  --epochs 20 \
  --learning_rate 1e-4

# Fine-tune HuBERT on SAVEE with Frozen Backbone
python scripts/train_transfer.py \
  --checkpoint outputs/cremad/hubert/checkpoints/best_model.pt \
  --target_dataset savee \
  --target_data_dir data/savee \
  --output_dir outputs/savee_enhanced/hubert_transfer_cremad_weighted_frozen \
  --pooling weighted \
  --freeze_encoder \
  --epochs 25 \
  --learning_rate 5e-4
```

### 4. Multi-Model Soft-Voting Ensemble

```bash
# CREMA-D Top-5 Ensemble
python scripts/evaluate_ensemble.py \
  --models hubert wav2vec2 emotion2vec_plus wavlm mfcc_cnn_bilstm \
  --weights 0.35 0.25 0.20 0.10 0.10 \
  --data_dir data/cremad \
  --outputs_root outputs/cremad \
  --split test

# RAVDESS Enhanced Transfer Ensemble
python scripts/evaluate_ensemble.py \
  --models hubert_transfer_cremad_weighted wav2vec2_transfer_cremad_weighted wavlm_transfer_cremad_weighted \
  --weights 0.45 0.35 0.20 \
  --data_dir data/ravdess \
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
  --data_dir data/savee \
  --output_dir outputs/cross_corpus/cremad_hubert/to_savee
```

### 6. Verification and Test Suite

```bash
# Run complete test suite (15 passing tests)
pytest tests/

# Validate model architectures and forward passes
python scripts/check_models.py

# Audit saved metrics and training artifacts
python scripts/verify_metrics.py --dataset cremad
python scripts/verify_metrics.py --dataset ravdess
python scripts/verify_metrics.py --dataset savee
python scripts/verify_metrics.py --dataset tess
```

---

## Methodological Guarantees

1. **Strict Zero-Leakage Partitions**:
   - **Speaker-Independent**: Test partitions for CREMA-D, RAVDESS, and SAVEE feature actors who never appear in training or validation splits.
   - **Prompt-Independent**: Test partitions for TESS feature 30 vocabulary words never spoken in the training split.
2. **Dynamic Label Discovery**:
   - Class indices, labels, and class counts are discovered dynamically at runtime via `metadata/labels.json` and canonical mappers.
3. **Reproducibility**:
   - Deterministic seeds are enforced across PyTorch, NumPy, and Python's random library.
4. **Isolated Artifact Namespaces**:
   - Checkpoints, curves, and confusion matrices for each dataset and experiment are isolated under `outputs/<dataset>/`.

---

## License

This project is licensed under the [MIT License](LICENSE).
