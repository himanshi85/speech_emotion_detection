# Benchmarking Self-Supervised Speech Representations, Learnable Layer Pooling, and Continuous Acoustic Telemetry for Multi-Corpus and Indic Speech Emotion Recognition

### A Controlled Empirical Evaluation Across CREMA-D, RAVDESS, SAVEE, TESS, and Indic Hindi Speech

**Himanshi (Primary Researcher) and Deep Learning Research Team**  
*Department of Computer Science and Engineering*  
*Project Repository: speech_emotion_detection (Branch: develop-v3)*

---

## Abstract

Speech Emotion Recognition (SER) is an important area within affective computing, conversational systems, and human-computer interaction. However, contemporary SER research confronts multiple empirical challenges. First, randomized dataset partitioning causes speaker identity leakage, which paralinguistic literature [21] has demonstrated artificially inflates experimental accuracy by allowing models to memorize familiar speaker characteristics. Second, deep architectures remain vulnerable to acoustic overfitting when trained on constrained speaker cohorts. Third, the literature exhibits a pronounced focus on Germanic and Romance languages, offering limited empirical evidence on cross-lingual transferability to morphologically rich Indic languages such as Hindi. Finally, categorical classification schemes alone fail to provide granular, interpretable measurements of continuous vocal behaviour.

To address these challenges, this study presents a standardized empirical evaluation comprising two decoupled experimental protocols across five speech corpora totaling 12,180 standardized audio recordings: (1) a multi-corpus English benchmark combining four established corpora (CREMA-D, RAVDESS, SAVEE, and TESS, totaling 11,318 canonical clips across 121 speakers) to evaluate cross-corpus generalization and layer-pooling dynamics, and (2) a cross-lingual transfer and in-domain adaptation study on an Indic speech corpus (862 standardized Hindi speech utterances across 14 unique speaker IDs curated from three open-access collections [31]–[33]). Speaker-disjoint evaluation is enforced for CREMA-D, RAVDESS, and SAVEE; TESS is evaluated under prompt-disjoint conditions on unseen vocabulary; and the Hindi specialist is evaluated on a stratified utterance-level split. Inspired by the lightweight probing methodology used in the SUPERB benchmark [2], we implement a Learnable Weighted Layer Pooling mechanism coupled with a linear classification probe across the 12 transformer encoder blocks of a frozen self-supervised foundation backbone (HuBERT-Base, training only 4,626 parameters, ~0.005% of network capacity). Empirical evaluation reveals that intermediate layers (Layers 9 to 11) receive approximately 31.95% of the learned normalized pooling weight (31.94% when summing the exported four-decimal rounded values, with unrounded softmax weights summing to 1.0000), indicating that the trained downstream probe assigned greater weight to intermediate representations under the evaluated protocol.

Across the 1,701 pooled multi-corpus test clips, a Universal HuBERT probe (initialized from the best CREMA-D HuBERT checkpoint and adapted on the combined 4-corpus dataset) achieves 68.31% aggregate accuracy (0.6779 Macro-F1, 68.61% UAR), outperforming the zero-shot CREMA-D baseline (60.61%) by +7.70 percentage points, alongside an unweighted corpus-level macro-average of 61.26% Accuracy and 57.54% UAR across the four diverse corpora. Furthermore, zero-shot cross-lingual evaluation of the English foundation model on the shared canonical subset of Hindi speech yields 27.62% accuracy and 31.76% Unweighted Average Recall (UAR) against a 25.00% 4-class chance floor. Supervised in-domain adaptation on the full 5-class Hindi space using a specialized CNN-BiLSTM architecture substantially increases test accuracy to 74.42% (75.19% via ensemble fusion) and UAR to 70.85% (70.56% ensemble) against a 20.00% 5-class chance floor (+46.80% single-model gain over zero-shot transfer). Finally, an auxiliary Audio Behaviour Analysis Engine extracts continuous acoustic telemetry (syllabic speaking rate, pause frequency, RMS energy, and fundamental pitch F0) to provide interpretable behavioural profiles without asserting clinical psychological diagnosis. The complete system is deployed as an Apple Silicon accelerated microservice paired with a web application featuring real-time audio waveform visualization.

**Keywords:** Speech Emotion Recognition, Self-Supervised Learning, Learnable Layer Pooling, Linear Probe, Hindi Speech Emotion, Cross-Lingual Transfer, Vocal Behaviour, Speaker Disjoint Split, HuBERT, Wav2Vec 2.0, CNN-BiLSTM.

---

## 1. Introduction & Research Motivation

Spoken human communication comprises both lexical content (the verbal message) and paralinguistic modulations (vocal tone, cadence, and inflection) [6], [16]. Speech Emotion Recognition (SER) aims to identify affective states (such as anger, joy, sadness, fear, or neutrality) from acoustic speech signals. While automatic speech recognition (ASR) systems have matured significantly, SER remains challenging because emotional expression varies substantially across speakers, regional dialects, and recording conditions [1], [13].

### 1.1 The Problem of Speaker Identity Leakage
A critical limitation in existing SER benchmarks is the use of randomized cross-validation [16], [21]. When speech segments from the same speaker appear in both the training and testing partitions, neural models tend to memorize speaker-specific vocal tract characteristics rather than generalizable emotional features. Consequently, models that report over 90% accuracy in random split evaluations frequently suffer substantial performance drops when tested on novel speakers. Valid evaluation necessitates strict speaker-independent partitions in which test speakers are entirely withheld during training [15], [21].

### 1.2 Indic and Low-Resource Language Representation
Most accessible SER benchmarks rely on English (e.g., IEMOCAP [28], RAVDESS [18], CREMA-D [17], SAVEE [19], TESS [20]) or German (e.g., EMO-DB) [16]. Indic languages, spoken by over 1.4 billion individuals, remain underrepresented in speech research [1], [3], [22], [23]. Hindi exhibits distinctive phonological properties, including phonemic vowel length contrasts, retroflex consonants, and syllable-timed stress patterns, which limit the cross-lingual transferability of models pre-trained predominantly on Western languages.

### 1.3 Interpretable Acoustic Behavioural Telemetry
Standard SER architectures typically output discrete emotion class probabilities, such as $P(\text{Happy}) = 0.85$. However, conversational systems, tele-counseling interfaces, and voice user interfaces benefit from continuous, interpretable acoustic measurements to assess measurable vocal behaviour without asserting direct clinical psychological diagnoses [5], [11], [12]:
1. **Speech Velocity (syllables/s):** Indicates psychomotor tempo and dynamic vocal cadence.
2. **Pause Frequency and Duration:** Reflects conversational hesitation, processing intervals, and structural fluency.
3. **Vocal Energy Variation:** Measures acoustic loudness dynamics and vocal projection intensity.
4. **Fundamental Pitch (F0) Variation:** Quantifies dynamic pitch inflection versus flattened vocal affect.

### 1.4 Research Questions (RQ)
This study addresses four primary research questions:
- **RQ1 (Layer-Wise Representation Dynamics):** How are affective vocal representations distributed across the depths of a frozen self-supervised speech transformer, and what relative weighting does learnable layer pooling converge upon when trained on multi-corpus speech?
- **RQ2 (Effect of Training Speaker Diversity):** What is the empirical association between training cohort speaker diversity and out-of-domain generalization performance on strictly unseen actors, when accounting for simultaneous variations in corpus conditions?
- **RQ3 (Cross-Lingual Transfer to Indic Speech):** To what degree do English multi-corpus representations transfer zero-shot to Hindi speech, and what quantitative performance gain is achieved via supervised in-domain adaptation?
- **RQ4 (Acoustic Behavioural Profiling):** What distinctive continuous acoustic profiles (syllabic speed, pause ratio, vocal energy, and fundamental pitch F0) characterize categorical emotion predictions, and how can auxiliary telemetry complement discrete classification without claiming clinical diagnostic validity?

---

## 2. Related Work & Literature Survey

This investigation synthesizes 33 scholarly sources across four core theoretical domains:

### 2.1 Indic and Hindi Speech Emotion Recognition
Early speech emotion recognition research in India relied predominantly on small private datasets evaluated with conventional classifiers such as Support Vector Machines (SVM) and Multi-Layer Perceptrons [4], [16]. Kotian and Singh (2026) [1] demonstrated that combining prosodic-behavioral descriptors (speaking rate, pitch perturbation, pause ratio, and energy dynamics) with acoustic representations enhanced classification accuracy and macro-F1 on Hindi speech under challenging acoustic conditions. Chauhan, Sharma, and Varma (2023) [3] introduced the MNITJ-SEHSD database, standardizing an Indic emotion corpus and highlighting acoustic overlap between anger and disgust resulting from shared high vocal intensity. Kawade and Jagtap (2024) [5] evaluated cross-lingual acoustic modeling across Indian speech corpora, demonstrating the effectiveness of combining multiple spectral, temporal, and voice quality descriptors with deep convolutional neural networks. Rathnayake et al. (2026) [22] and Alam Monisha and Sultana (2022) [23] provided comprehensive surveys on the unique acoustic-phonetic challenges and database resources in low-resource Indo-Aryan and Dravidian speech emotion recognition.

### 2.2 Self-Supervised Speech Representation Learning & Probing
Self-supervised learning has established powerful representations for speech tasks. Models such as Wav2Vec 2.0 (Baevski et al., 2020) [9] and HuBERT (Hsu et al., 2021) [8] learn representations from thousands of hours of unlabeled audio through contrastive loss or masked cluster prediction. Yang et al. (2021) [2] introduced the SUPERB benchmark, establishing standard evaluation methodologies for speech representation learning and demonstrating that learnable layer-weighted combinations of intermediate representations consistently outperform fixed top-layer embeddings across diverse speech classification tasks. Pepino, Riera, and Ferrer (2021) [27] and Sun et al. (2024) [30] demonstrated the efficacy of fine-tuning pre-trained representations for downstream emotion recognition, while Wang and Yang (2025) [14] integrated fine-tuned Wav2vec 2.0 with neural controlled differential equation classifiers. Recent investigations into speech representation learning (such as emotion2vec [6] and BEATs [7]) further indicate that different speech tasks rely on distinct representational abstractions across model depth. Probing studies by Pasad, Chou, and Livescu (2021) [24] demonstrated that different acoustic and linguistic information is distributed non-uniformly across self-supervised speech-representation layers, motivating layer-wise probing rather than relying exclusively on the final representation. These findings motivate the Learnable Weighted Layer Pooling approach used in this work.

### 2.3 Vocal Behavioural Feature Integration
Standardized acoustic parameter sets have long provided interpretable metrics for speech analysis. Eyben et al. (2016) defined the Geneva Minimalistic Acoustic Parameter Set (GeMAPS) and extended GeMAPS (eGeMAPS) [12], standardizing 88 acoustic descriptors across frequency, energy, and temporal domains. Chowdhury, Ramanna, and Kotecha (2025) [11] showed that integrating hand-crafted acoustic prosody with lightweight deep neural ensemble architectures improved interpretability and performance across multiple SER benchmarks.

### 2.4 Speaker Disjoint Protocols and Generalization
Goel, Hira, and Gupta (2024) [21] examined the challenge of unseen speaker generalization in SER, evaluating pretrained speech encoders (HuBERT, Wav2Vec 2.0, WavLM) under leave-speaker-out multilingual conditions and demonstrating that standard random train/test splits cause neural models to overfit speaker identity rather than true affective cues. Whereas Goel et al. focused on multi-task co-attention, the present investigation evaluates a unified multi-corpus English benchmark under canonicalized emotion mappings, analyzes layer-wise pooling weights, and quantifies both zero-shot cross-lingual transfer and supervised in-domain adaptation on Hindi speech. Hashem, Arif, and Alghamdi (2023) [15] and Akçay and Oğuz (2020) [16] conducted systematic reviews detailing how cross-corpus evaluation protocols reveal severe performance degradation when models encounter novel recording environments. Wagner et al. (2018) [25] empirically evaluated hand-crafted features versus learned representations across paralinguistic tasks, finding that acoustic descriptors provide vital complementarity to deep representations, while Latif et al. (2023) [26] surveyed deep representation learning paradigms for disentangling speaker identity from affective prosody.

---

## 3. Dataset Ecosystem & Partitioning Protocols

To ensure rigorous evaluation, five distinct corpora comprising 12,180 standardized audio files were curated, preprocessed, and partitioned. Audio files were resampled and standardized to 16,000 Hz sampling rate, single-channel (mono), 16-bit PCM WAV format. Table 1 summarizes the dataset ecosystem.

### 3.1 Multi-Corpus English Canonical Standardization
The English multi-corpus benchmark incorporates four established speech emotion repositories: CREMA-D [17] (7,442 utterances, 91 actors), RAVDESS [18] (1,440 utterances, 24 actors), SAVEE [19] (480 utterances, 4 actors), and TESS [20] (2,800 utterances, 2 actresses). Across these four datasets, raw clips total 12,162. To establish an aligned label space, emotions are mapped to a 6-class canonical ontology: neutral, happy, sad, angry, fear, and disgust. Non-shared emotions (such as calm and surprise in RAVDESS and SAVEE, totaling 844 clips) were excluded prior to model training, yielding a standardized multi-corpus pool of 11,318 audio clips from 121 speakers.

### 3.2 Indic Hindi Dataset Provenance & Partitioning Protocol
The Hindi evaluation utilizes 862 standardized speech utterances (1.80 hours total) curated from three open-access Indic speech repositories [31]–[33]: (1) Indian TTS Emotion Corpus (`sarthwa8/indian-tts-emotion-60min` on HuggingFace [31], licensed under CC BY 4.0, contributing 130 clips across 8 speaker IDs `hi_spk01` through `hi_spk08`); (2) Project Vaani Indian Speech Corpus (`ghostieee11/vaani-speech-corpus` on HuggingFace [32], contributing 465 standardized segments derived from the Hindi subset under speaker ID `hi_kahanisuno`, with dataset card license listed as 'other'); and (3) RapidOrc Audio Emotion Detection Dataset (`RapidOrc121/audio-emotion-detection-dataset` on HuggingFace [33], licensed under CC BY 4.0, contributing 267 clips across 5 speaker IDs `rapidorc_spk_0` through `rapidorc_spk_4`). Across all three source collections, the combined Hindi corpus contains 14 unique speaker IDs spanning five discrete emotion classes: neutral (363 clips), calm (160 clips), sad (158 clips), angry (105 clips), and happy (76 clips).

The Hindi corpus was partitioned using an utterance-level stratified split (stratified by emotion class): 604 training clips (70.1%), 129 validation clips (15.0%), and 129 test clips (15.0%). In contrast to the speaker-disjoint splits of CREMA-D, RAVDESS, and SAVEE, utterances from the 14 Hindi speakers appear across train, validation, and test partitions, reflecting an utterance-level evaluation protocol. Table 2 documents the exact source provenance and speaker distribution.

#### Table 1: Standardized Dataset Ecosystem and Partitioning Specifications
| Corpus | Utterances | Language | Speakers / Scope | Split Protocol | Classes |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **CREMA-D** | 7,442 | English (US) | 91 Diverse Actors | Actor-Disjoint (13 Unseen Actors) | 6 Canonical Classes |
| **RAVDESS** | 1,440 | English (NA) | 24 Professional Actors | Actor-Disjoint (4 Unseen Actors) | 8 Classes (6 Shared) |
| **SAVEE** | 480 | English (UK) | 4 British Actors | Actor-Disjoint (Actor KL Unseen) | 7 Classes (6 Shared) |
| **TESS** | 2,800 | English (CA) | 2 Actresses, 200 Words | Prompt-Disjoint (30 Unseen Words) | 7 Classes (6 Shared) |
| **Hindi SER** | 862 | Hindi (Indic) | 14 Unique Speaker IDs | Stratified Split (604/129/129) | 5 Discrete Classes |
| **Total Evaluated** | **12,180** | **Multilingual** | **135 Total Speakers** | **Multi-Corpus Benchmark** | **Unified Ontologies** |

*\*Note: Across the four English source corpora, raw clips total 12,162. Standardizing onto the 6 shared canonical classes excludes 844 non-shared clips, yielding 11,318 English clips. Combined with the 862 standardized Hindi clips, the complete evaluation encompasses 12,180 audio clips.*

#### Table 2: Provenance and Speaker Distribution of Indic Hindi Speech Emotion Corpus
| Source Collection | Repository Identifier / Source | Segments | Speaker IDs | Emotions Covered | Licensing / Provenance |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Indian TTS Emotion** | `sarthwa8/indian-tts-emotion-60min` | 130 | 8 (`hi_spk01-08`) | Neutral, Happy, Sad, Angry, Calm | CC BY 4.0 (Open Access) [31] |
| **Project Vaani Subset** | `ghostieee11/vaani-speech-corpus` | 465 | 1 (`hi_kahanisuno`) | Neutral, Calm, Sad | Open Scholarly Access (license: 'other') [32] |
| **RapidOrc Emotion** | `RapidOrc121/audio-emotion-detection-dataset` | 267 | 5 (`rapidorc_spk_0-4`) | Neutral, Happy, Sad, Angry | CC BY 4.0 (Open Access) [33] |
| **Integrated Hindi Pool** | `data/hindi/` (develop-v3) | **862** | **14 Unique Speaker IDs** | **5 Canonical Discrete Classes** | **Stratified Partition (604/129/129)** |

*\*Note: For Project Vaani, 465 represents the count of standardized audio segments derived from the Hindi subset of the source corpus. Speaker counts reflect distinct speaker IDs identified in source metadata.*

---

## 4. Methodology & Model Architecture

The system architecture features a dual-branch processing pipeline: (1) a Neural Acoustic Classifier Branch processing audio through pre-trained self-supervised transformer backbones with learnable weighted layer pooling (Universal HuBERT) or CNN-BiLSTM networks (Hindi Specialist), and (2) an Audio Behaviour Analysis Engine extracting continuous prosodic and temporal dynamics (pYIN F0 intonation, syllabic tempo via onset peaks, pause frequency via energy VAD, and frame-level RMS loudness).

```
                            AUDIO INPUT STANDARDIZATION
                       16 kHz Mono PCM WAV (12,180 clips)
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
┌──────────────────────────────────────┐     ┌───────────────────────────────────┐
│     NEURAL SER CLASSIFIER BRANCH     │     │     ACOUSTIC BEHAVIOUR BRANCH     │
│                                      │     │                                   │
│  [Universal HuBERT Branch]           │     │  Raw Audio Prosodic Telemetry:    │
│  • Raw 16 kHz Audio Waveform         │     │  • Syllabic Rate (syl/s & WPM)    │
│  • 12 Transformer Layers (Frozen)    │     │  • Pause Ratio (%) via Energy VAD │
│  • Learnable Weighted Pooling L1-L12 │     │  • Vocal Loudness (RMS dB)        │
│  • CREMA-D Pre-trained Init          │     │  • Pitch Tracking (pYIN F0 Hz)    │
│                                      │     │                                   │
│  [Hindi Specialist Branch]           │     │  Behavioural Synthesis:           │
│  • 40 MFCCs (32-ms win, 10-ms hop)   │     │  • Rule-based diagnostic profile  │
│  • 3-Layer 1D CNN + 2-Layer BiLSTM   │     │    (Engaged, Calm, Hesitant, etc.)│
│                                      │     └───────────────────────────────────┘
│  Downstream Classification Heads:    │
│  • Universal Head: 6 Classes         │
│  • Hindi Specialist: 5 Classes       │
└──────────────────────────────────────┘
```
*Figure 1: End-to-End System Architecture with Dual-Branch Neural SER and Acoustic Behaviour Analysis.*

### 4.1 Learnable Weighted Layer Pooling & Linear Probing
Inspired by the lightweight probing methodology used in the SUPERB benchmark [2] and Pepino et al. [27], we adopt a learnable layer-wise weighted sum across all $L = 12$ transformer encoder representations. In accordance with standard HuggingFace transformer interfaces, `outputs.hidden_states` returns 13 tensors (Layer 0 feature projection followed by 12 transformer encoder blocks). The pooling module explicitly selects the last 12 tensors (`hidden_states[-12:]`), pooling the outputs of transformer encoder blocks 1 through 12 ($l \in \{1, \dots, 12\}$) and cleanly excluding the initial CNN feature projection. The Universal HuBERT model is initialized from the best CREMA-D-trained HuBERT checkpoint (`outputs/cremad/hubert/checkpoints/best_model/model.pt`, logged as `HuBERT (Transfer from CREMAD)`) and subsequently adapted on the combined 4-corpus training set with frozen backbone weights:

$$e_t = \sum_{l=1}^{L} lpha_l h_t^{(l)}, \quad lpha_l = rac{\exp(w_l)}{\sum_{j=1}^{L} \exp(w_j)}$$

where $h_t^{(l)} \in \mathbb{R}^D$ denotes the hidden representation at time frame $t$ from layer $l$, and $w_l \in \mathbb{R}$ is an unconstrained learnable scalar initialized uniformly. Time-dimension aggregation yields utterance embedding $u$:

$$u = rac{1}{\sum_{t=1}^T m_t} \sum_{t=1}^{T} m_t e_t$$

The classification probe projects $u$ through a linear transformation to compute class probabilities:

$$\hat{y} = 	ext{softmax}(W u + b)$$

### 4.2 Lightweight CNN-BiLSTM Specialist Architecture
For low-resource Indic speech, we employ a compact CNN-BiLSTM network. Audio waveforms are transformed into 40-dimensional Mel-Frequency Cepstral Coefficients (MFCC) extracted with a 32-ms FFT window (512 samples at 16 kHz) and a 10-ms hop length (160 samples):
1. **Feature Extraction:** 40 MFCCs, 32-ms window, 10-ms hop.
2. **Temporal Convolution:** 3-layer 1D CNN with filter banks $\{64, 128, 256\}$, kernel size 5, stride 1, padding 2, BatchNorm, ReLU, and Dropout ($p=0.3$).
3. **Sequential Modeling:** 2-layer Bidirectional LSTM with hidden dimension 128 per direction (effective 256 dimensions).
4. **Classification Head:** Masked temporal average pooling followed by linear projection ($256 	o 5$ classes).
5. **Parameter Efficiency:** 923,717 total trainable parameters (~924K, 100% trainable).

### 4.3 Audio Behaviour Analysis Engine Formulation
The behaviour engine extracts continuous telemetry:
- **Speaking Speed:** Syllables per second:
  $$	ext{Speed} = rac{N_{	ext{syllables}}}{T_{	ext{active}}}, \quad 	ext{WPM} = rac{	ext{Speed}}{1.5} 	imes 60$$
- **Pause Ratio:** Energy-based voice activity detection silence duration percentage:
  $$	ext{Pause Ratio} = rac{T_{	ext{pause}}}{T_{	ext{total}}} 	imes 100\%$$
- **Vocal Intensity (RMS dB):**
  $$	ext{RMS}_{	ext{dB}} = 20 \log_{10}(	ext{RMS} + \epsilon)$$
- **Pitch Frequency (F0 via pYIN):**
  $$\sigma_{F0} = \sqrt{rac{1}{M} \sum_{m=1}^M (F0[m] - \overline{F0})^2}$$

---

## 5. Experimental Setup & Evaluation Metrics

All experiments were conducted using PyTorch 2.x with Metal Performance Shaders (MPS) hardware acceleration on Apple Silicon. The training framework employs the AdamW optimizer with a LambdaLR schedule consisting of linear warm-up (`warmup_ratio = 0.1`) followed by linear learning rate decay to zero. For the Universal HuBERT probe, the model was initialized from the best CREMA-D-trained HuBERT checkpoint (`outputs/cremad/hubert/checkpoints/best_model/model.pt`, logged as `HuBERT (Transfer from CREMAD)`), with the backbone parameters strictly frozen (`encoder_learning_rate = 0.0`), and the linear classification head and layer pooling weights adapted on the combined 4-corpus dataset at a classifier learning rate of 3e-4 with gradient accumulation of 4 steps (effective batch size 64) for 10 epochs (early stopping patience = 4). The CNN-BiLSTM was optimized at a learning rate of 1e-3 with batch size 32 for 25 epochs (early stopping patience = 5). Class-weighted cross-entropy loss was applied to mitigate dataset class imbalances.

#### Table 3: Verified Experimental & Hyperparameter Reproducibility Specifications
| Configuration Parameter | Universal HuBERT (CREMA-D-Init Frozen Probe) | CNN-BiLSTM (Hindi Specialist) |
| :--- | :---: | :---: |
| **Initialization Checkpoint** | CREMA-D HuBERT Checkpoint Transfer | Random Xavier Initialization |
| **Base Architecture / Backbone** | HuBERT-Base (`facebook/hubert-base-ls960`) | 3-Layer 1D CNN + 2-Layer BiLSTM |
| **Input Audio Representation** | Raw Audio Waveform (16 kHz, Mono PCM) | 40 MFCCs (32-ms FFT win, 10-ms hop) |
| **Backbone Parameter Status** | Frozen (`encoder_lr = 0.0`, 0 updates) | Fully Trainable (End-to-End optimization) |
| **Trainable Parameters** | 4,626 parameters (~0.005% of 94.7M) | 923,717 parameters (~924K, 100% trainable) |
| **Target Emotion Classes** | 6 Canonical Classes (English Pool) | 5 Discrete Classes (Hindi Corpus) |
| **Optimizer & Weight Decay** | AdamW (weight decay = 0.01) | AdamW (weight decay = 0.01) |
| **Learning Rate (Head / Net)** | 3e-4 (Linear Probe + Softmax Layer Weights) | 1e-3 (Full Network) |
| **Learning Rate Schedule** | LambdaLR (Linear Warm-up 10% + Linear Decay) | LambdaLR (Linear Warm-up 10% + Linear Decay) |
| **Batching Strategy** | Batch Size = 16, Gradient Accum = 4 (Eff. 64) | Batch Size = 32, Gradient Accum = 1 |
| **Maximum Training Epochs** | 10 Epochs (Early Stopping Patience = 4) | 25 Epochs (Early Stopping Patience = 5) |
| **Hardware & Acceleration** | Apple Silicon MPS (Metal Performance Shaders) | Apple Silicon MPS (Metal Performance Shaders) |

---

## 6. Benchmark Results & Comparative Analysis

### 6.1 Universal Multi-Corpus Linear Probe Benchmark
To evaluate whether a unified representation can generalize across diverse acoustic environments, accents, and recording conditions, a Universal HuBERT probe was initialized from the best CREMA-D HuBERT checkpoint (`outputs/cremad/hubert/checkpoints/best_model/model.pt`, logged as `HuBERT (Transfer from CREMAD)`) and subsequently adapted on the combined four-corpus training set, comprising 103 unique training speaker IDs across CREMA-D, RAVDESS, SAVEE, and TESS (TESS uses prompt-disjoint rather than speaker-disjoint evaluation), and evaluated against 1,701 unseen multi-corpus test utterances (1,060 CREMA-D + 360 TESS + 176 RAVDESS + 105 SAVEE).

Across the 1,701 pooled test clips, the Universal HuBERT probe achieves 68.31% aggregate accuracy (0.6779 Macro-F1, 68.61% UAR), outperforming the zero-shot CREMA-D HuBERT baseline (which achieves 60.61% accuracy, 0.6031 Macro-F1, and 60.54% UAR when transferred directly to the multi-corpus test set) by an absolute margin of +7.70 percentage points. This gain reflects the combined effect of multi-corpus supervised adaptation and learnable layer pooling over the single-corpus initialization. Because the pooled test set is weighted by dataset size (dominated by CREMA-D at 62.3% of clips), we also calculate the unweighted corpus-level macro-average across the four distinct corpora: 61.26% Accuracy, 0.5755 Macro-F1, and 57.54% UAR (CREMA-D: 72.45% acc / 72.03% UAR; TESS: 68.89% acc / 68.89% UAR; RAVDESS: 52.27% acc / 51.14% UAR; SAVEE: 51.43% acc / 38.10% UAR). Table 4 reports the benchmark leaderboard alongside sub-cohort breakdowns on unseen test partitions.

#### Table 4: Universal Multi-Corpus Test Leaderboard (1,701 Multi-Corpus Test Clips)
| Model / Evaluation Strategy | Test Accuracy | Macro-F1 | Test UAR | Status / Scope |
| :--- | :---: | :---: | :---: | :--- |
| **Universal HuBERT (CREMA-D-Init Frozen Probe)** | **68.31%** | **0.6779** | **68.61%** | **Pooled Aggregate (4.1x chance)** |
| **Zero-Shot CREMA-D HuBERT Baseline** | 60.61% | 0.6031 | 60.54% | Direct Multi-Corpus Transfer |
| **Corpus-Level Unweighted Macro-Average (4 Corpora)** | **61.26%** | **0.5755** | **57.54%** | **Balanced Cross-Corpus Average** |
| Sub-Cohort: CREMA-D (1,060 clips, 13 actors) | 72.45% | 0.7232 | 72.03% | Unseen Diverse Actors (IDs 1079-1091) |
| Sub-Cohort: TESS (360 clips, 30 words) | 68.89% | 0.6771 | 68.89% | Prompt-Disjoint Vocabulary Words |
| Sub-Cohort: RAVDESS (176 clips, 4 actors) | 52.27% | 0.5018 | 51.14% | Unseen Professional Actors (21-24) |
| Sub-Cohort: SAVEE (105 clips, 1 actor) | 51.43% | 0.3999 | 38.10% | Single-Speaker SAVEE (Actor KL) |
| Random Chance Baseline | 16.67% | 0.1667 | 16.67% | Theoretical 6-Class Floor |

### 6.2 Single-Corpus In-Domain Baselines
#### Table 5: In-Domain Benchmark Performance Across Individual Corpora
| Dataset | Best Model | Accuracy | Macro-F1 | UAR | Chance Floor |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **CREMA-D** | Top-5 Soft-Voting Ensemble | 75.57% | 0.7594 | 75.61% | 16.67% |
| **RAVDESS** | Transfer Ensemble (CREMA-D) | 73.75% | 0.7207 | 72.27% | 12.50% |
| **SAVEE (Single Speaker)** | Transfer Ensemble (CREMA-D) | 51.67% | 0.3860 | 40.48% | 14.29% |
| **TESS (Controlled Prompt)** | TESS-only HuBERT / W2V2 | 100.00% | 1.0000 | 100.00% | 14.29% |
| **Hindi SER (5 Classes)** | CNN-BiLSTM Specialist | 74.42% | 0.7201 | 70.85% | 20.00% |
| **Hindi SER (5 Classes)** | Top-2 Ensemble (CNN-BiLSTM + LSTM) | 75.19% | 0.7136 | 70.56% | 20.00% |
| **Combined (Multi-Corpus)** | Universal HuBERT (CREMA-D-Init Probe) | 68.31% | 0.6779 | 68.61% | 16.67% |

### 6.3 Technical Analysis of Wav2Vec2-XLS-R-300M Representation Mismatch
Across all evaluated corpora, Wav2Vec2-XLS-R-300M [10] performed near random chance (13.33% on RAVDESS, 24.43% on CREMA-D, 12.50% on SAVEE, and 19.76% on TESS), underperforming shallow MFCC baselines:
1. **ASR Invariant Pre-training Objective:** One possible explanation is that the ASR-oriented pretraining objective encourages phonetic invariance that may reduce the linear separability of affect-related acoustic variation in the frozen final-layer representation.
2. **Top-Layer Specialization:** Unlike our HuBERT framework which incorporates learnable layer pooling across intermediate depths, the frozen XLS-R baseline extracted features exclusively from its 24th (final) layer. This outcome is consistent with layer-probing findings by Pasad, Chou, and Livescu (2021) [24], which demonstrated that paralinguistic and emotional information concentrates within intermediate transformer representations before upper layers specialize toward phonetic invariance.
3. **Capacity-to-Sample Mismatch:** Projecting a frozen 1024-dimensional representation from a 317M-parameter model onto tiny target datasets without layer-wise adaptation creates an acute representation mismatch that prevents effective linear separation.

---

## 7. Empirical Findings & Ablation Studies

### 7.1 Effect of Training Speaker Diversity on Cross-Speaker Generalization
Comparing performance across SAVEE (3 training actors), RAVDESS (20 training actors), and CREMA-D (78 training actors) demonstrates a consistent relationship between speaker cohort size and generalization capability on strictly unseen test speakers. Evaluating HuBERT models trained from scratch across these datasets reveals that on SAVEE (3 training speakers), HuBERT achieved only 25.83% test accuracy (Macro-F1 0.0795) due to vocal tract overfitting on the limited speaker cohort. Expanding the training cohort to 20 actors in RAVDESS elevated scratch HuBERT accuracy to 32.50% (and 68.75% for the scratch ensemble). In CREMA-D, with 78 training actors, HuBERT from scratch reached 71.98% accuracy (and 75.57% for the ensemble). These empirical results indicate that broader speaker diversity during training is associated with improved speaker-independent generalization across unseen cohorts, whereas training on minimal speaker cohorts risks acute speaker identity memorization. Because corpus identity, recording conditions, lexical content, and training-set size vary simultaneously with speaker count, the comparison should not be interpreted as a causal estimate of speaker diversity.

### 7.2 Layer Weight Distribution Across Transformer Depth
Softmax weights $lpha$ across the 12 transformer encoder blocks of the Universal HuBERT model, extracted directly from the trained checkpoint (exported to `outputs/combined/universal_hubert_weighted_frozen/metrics/layer_weights.csv` in the repository):
- **Early Layers (Layers 1 to 4):** Weights remain basal ($lpha_1 = 0.0707, lpha_2 = 0.0710, lpha_3 = 0.0711, lpha_4 = 0.0712$, representing 7.07% to 7.12%), capturing low-level spectro-temporal acoustics.
- **Intermediate Transition (Layers 5 to 8):** Weights steadily increase ($lpha_5 = 0.0713, lpha_6 = 0.0717, lpha_7 = 0.0725, lpha_8 = 0.0757$, representing 7.13% to 7.57%), reflecting progressive harmonic abstraction.
- **Intermediate Prosodic Zone (Layers 9 to 11):** Weights reach their empirical maximum ($lpha_9 = 0.1001, lpha_{10} = 0.1107, lpha_{11} = 0.1086$), receiving approximately 31.95% of the total normalized layer weight (31.94% when summing the exported four-decimal rounded values: 10.01% + 11.07% + 10.86%). The optimizer assigned its highest weight to Layer 10 ($lpha_{10} = 0.1107$, 11.07%), indicating that the trained downstream probe assigned greater weight to Layers 9–11 under the evaluated protocol, consistent with prior literature [2, 24] noting affective information concentration in intermediate transformer representations.
- **Final Layer (Layer 12):** Weight decreases slightly to $lpha_{12} = 0.1053$ (10.53%) relative to Layer 10 as representation space shifts toward discrete phonetic classification.
- **Normalization Verification:** The unrounded softmax weights sum to 1.0000; displayed values are rounded to four decimal places (summing to 99.99% across all 12 layers due to rounding: 7.07% + 7.10% + 7.11% + 7.12% + 7.13% + 7.17% + 7.25% + 7.57% + 10.01% + 11.07% + 10.86% + 10.53%).

#### Table 6: Layer-Wise Softmax Attention Weight Distribution (HuBERT-Base)
| Layer Index | Softmax Weight | Percentage | Interpretive Context (Literature-Informed) |
| :--- | :---: | :---: | :--- |
| **Layer 1** | 0.0707 | 7.07% | Waveform envelope & low-level spectral energy |
| **Layer 2** | 0.0710 | 7.10% | Formant structures and spectral slope |
| **Layer 3** | 0.0711 | 7.11% | Pitch frequency baseline estimation |
| **Layer 4** | 0.0712 | 7.12% | Spectral flux and voice onset timing |
| **Layer 5** | 0.0713 | 7.13% | Phonetic-prosodic transition boundary |
| **Layer 6** | 0.0717 | 7.17% | Intermediate harmonic structure encoding |
| **Layer 7** | 0.0725 | 7.25% | Broad phonetic category separation |
| **Layer 8** | 0.0757 | 7.57% | Prosodic phrasing & cadence abstraction |
| **Layer 9** | **0.1001** | **10.01%** | Emotional inflection & macro-prosodic features |
| **Layer 10** | **0.1107** | **11.07%** | Associated with highest learned pooling weight (11.07%) |
| **Layer 11** | **0.1086** | **10.86%** | Global utterance affect & speaker dynamics |
| **Layer 12** | 0.1053 | 10.53% | Phonetic discrimination & lexical alignment |
| **Total Sum** | **1.0000** | **99.99%\*** | The unrounded softmax weights sum to 1.0000 (\*99.99% due to 4-decimal rounding) |

### 7.3 Cross-Lingual Adaptation to Indic Hindi Speech
To evaluate cross-lingual transferability, the English-trained Universal HuBERT model was evaluated zero-shot on the unseen Hindi test split. Under closed-set cross-corpus evaluation, the 6-class English head evaluates over the intersection of shared canonical classes (angry, happy, neutral, sad), filtering 105 test clips (24 calm clips without direct English 6-class analogue are excluded from this closed-set slice). Universal HuBERT achieves 27.62% accuracy and 31.76% UAR without any target fine-tuning, exceeding the 25.00% 4-class random chance baseline.

In contrast, supervised adaptation using the specialized CNN-BiLSTM architecture trained directly on the 5-class Hindi training partition achieves 74.42% test accuracy, 0.7201 Macro-F1, and 70.85% UAR across all 129 test clips (with the Top-2 ensemble reaching 75.19% accuracy and 70.56% UAR against a 20.00% 5-class chance floor). This represents an absolute gain of 46.80 percentage points (47.57 points for the ensemble) over zero-shot transfer, demonstrating the substantial value of in-domain supervised adaptation for the evaluated Hindi task.

---

## 8. Speech Behavioural Intelligence Profiling

Continuous acoustic telemetry provides objective measurements of speech behaviour that systematically characterize categorical emotional states without asserting clinical psychological diagnosis. Across the evaluated audio corpus, acoustic telemetry extracted by the Audio Behaviour Analysis Engine reveals pronounced, interpretable differences in vocal cadence, hesitation intervals, and acoustic intensity across emotion classes. Table 7 summarizes these empirical telemetry profiles across the five evaluated emotion categories:

#### Table 7: Acoustic Behavioural Telemetry Profiles Across Discrete Emotion Categories
| Emotion Category | N | Speaking Speed (syl/s) | Pause Ratio (%) | RMS Energy (dB) | Mean Pitch F0 (Hz) | Observed Acoustic Behaviour Profile |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Angry** | 15 | 2.82 ± 0.21 | 26.5 ± 10.0% | -27.8 ± 3.2 dB | 224.7 ± 98.7 Hz | Elevated pitch frequency (224.7 Hz), wide pitch variation (std: 56.4 Hz), reduced hesitation |
| **Calm** | 24 | 3.15 ± 0.55 | 34.4 ± 13.1% | -27.1 ± 3.1 dB | 162.8 ± 44.5 Hz | Highest pause ratio (34.4%), measured vocal cadence, lower pitch baseline (162.8 Hz) |
| **Happy** | 12 | 2.72 ± 0.17 | 24.5 ± 7.5% | -23.7 ± 3.6 dB | 200.8 ± 81.7 Hz | Highest vocal loudness (-23.7 dB RMS), lowest pause ratio (24.5%), high pitch (200.8 Hz) |
| **Neutral** | 55 | 2.90 ± 0.29 | 34.0 ± 10.5% | -27.4 ± 3.0 dB | 165.7 ± 73.0 Hz | Baseline conversational cadence (2.90 syl/s), moderate energy (-27.4 dB), stable pitch |
| **Sad** | 23 | 2.89 ± 0.44 | 28.6 ± 11.0% | -29.6 ± 6.7 dB | 165.6 ± 54.1 Hz | Lowest acoustic energy (-29.6 dB RMS), attenuated vocal dynamics, moderate pauses |

*\*Note: Empirical acoustic telemetry extracted directly from all 129 evaluation audio clips by `scripts/extract_behavior_profiles.py` (archived in `outputs/behavior/emotion_profiles.csv`). Values represent Mean ± Standard Deviation.*

---

## 9. System Deployment Architecture & Hardware Latency Benchmark

The complete framework is implemented as an Apple Silicon accelerated microservice paired with a minimal web application. Inference latency was benchmarked on an Apple M-series processor utilizing Metal Performance Shaders (MPS) hardware acceleration under PyTorch 2.x with batch size = 1 (simulating single-clip real-time streaming audio ingestion). Timing was measured over 10 warm-up runs followed by 100 consecutive benchmark iterations on standardized 3.0-second audio clips:
- **Backend Microservice (FastAPI):** Model registry serving the Hindi Specialist (CNN-BiLSTM) and Universal SER models. The lightweight CNN-BiLSTM specialist achieved an average inference latency of 19.94 ms per clip (std: 1.2 ms), while the 12-layer Universal HuBERT model achieved 191.44 ms per clip (std: 5.6 ms), validating that both models operate comfortably within real-time streaming processing budgets.
- **Frontend User Interface:** Web interface with audio recording, live waveform visualization, emotion probability radar charts, and behavioral telemetry display.

---

## 10. Discussion & Limitations

1. **Acoustic Generalization Gap:** A persistent challenge is the performance differential between single-corpus in-domain benchmarks and out-of-domain evaluation. Models achieving >90% on single-corpus random splits frequently degrade to 50–70% when evaluated on unseen speakers and recording environments.
2. **Computational Overhead of Foundation Models:** While HuBERT provides rich multi-level abstractions, its 191.44 ms latency and 94.7M parameters require substantial compute relative to the 19.94 ms, 924K-parameter CNN-BiLSTM specialist.
3. **Indic Dialectal Diversity:** The Hindi evaluation was conducted across 14 unique speaker IDs; regional dialectal variations across northern and central India require broader multi-dialect data collection.
4. **Behavioral Telemetry Non-Diagnostic Scope:** The Audio Behaviour Analysis Engine is intended as an objective measurement tool to characterize vocal dynamics, not as a psychological assessment instrument.

---

## 11. Conclusion

This paper presented an empirical evaluation of speech emotion recognition and vocal behavioural profiling across five speech corpora totaling 12,180 standardized audio clips:
1. **Learnable Weighted Layer Pooling:** The learned pooling mechanism assigned its highest aggregate weight to Layers 9–11, which together received approximately 31.95% of the normalized layer weight. This indicates that the downstream probe preferentially weighted these intermediate representations under the evaluated multi-corpus protocol.
2. **Effect of Training Speaker Diversity:** Broad multi-speaker training cohorts are associated with improved generalization: models trained on minimal speaker cohorts overfit individual speaker vocal tract geometry, whereas diverse cohorts support robust speaker-independent evaluation.
3. **Cross-Lingual Transfer & Supervised Adaptation:** English pre-trained models transfer moderately above chance (27.62% vs. 25.00% floor) to Hindi speech, but supervised adaptation using specialized CNN-BiLSTM networks achieves 74.42% accuracy (75.19% via ensemble fusion), representing a +46.80% single-model performance gain.
4. **Continuous Behavioural Telemetry:** Combining discrete emotion classification with continuous acoustic measurements (speaking rate, pause ratio, RMS energy, and pitch variability) provides interpretable vocal characterization to complement categorical predictions.

---

## References

- [1] S. Kotian and S. Singh, "Evaluating the Impact of Behavioural Features on Hindi Speech Emotion Recognition: A Multimodal Deep Learning Approach," *International Journal of Applied Artificial Intelligence and Robotics*, vol. 2, no. 1, art. 9, pp. 1–15, Mar. 2026, doi: [10.67745/ijaic.v2i1.9](https://doi.org/10.67745/ijaic.v2i1.9).
- [2] S.-w. Yang, P.-H. Chi, Y.-S. Chuang, C.-I. J. Lai, K. Lakhotia, Y. Y. Lin, A. T. Liu, J. Shi, X. Chang, G.-T. Lin et al., "SUPERB: Speech Processing Universal PERformance Benchmark," in *Proc. Interspeech 2021*, Brno, Czech Republic, 2021, pp. 1194–1198, doi: [10.21437/Interspeech.2021-1775](https://doi.org/10.21437/Interspeech.2021-1775).
- [3] K. Chauhan, K. K. Sharma, and T. Varma, "MNITJ-SEHSD: A Hindi Emotional Speech Database," in *Proc. 2023 International Conference on Communication, Circuits, and Systems (IC3S)*, Bhubaneswar, India, 2023, pp. 1–6, doi: [10.1109/IC3S57698.2023.10169497](https://doi.org/10.1109/IC3S57698.2023.10169497).
- [4] P. Mehra and S. K. Verma, "BERIS: An mBERT-based Emotion Recognition Algorithm from Indian Speech," *ACM Transactions on Asian and Low-Resource Language Information Processing*, vol. 21, no. 5, art. 106, pp. 1–19, Apr. 2022, doi: [10.1145/3517195](https://doi.org/10.1145/3517195).
- [5] R. Kawade and S. Jagtap, "Indian Cross Corpus Speech Emotion Recognition Using Multiple Spectral-Temporal-Voice Quality Acoustic Features and Deep Convolution Neural Network," *Revue d'Intelligence Artificielle*, vol. 38, no. 3, pp. 913–927, Jun. 2024, doi: [10.18280/ria.380318](https://doi.org/10.18280/ria.380318).
- [6] Z. Ma, Z. Zheng, J. Ye, J. Li, Z. Gao, S. Zhang, and X. Chen, "emotion2vec: Self-Supervised Pre-Training for Speech Emotion Representation," in *Findings of the Association for Computational Linguistics: ACL 2024*, Bangkok, Thailand, 2024, pp. 15747–15760, doi: [10.18653/v1/2024.findings-acl.931](https://doi.org/10.18653/v1/2024.findings-acl.931).
- [7] S. Chen, Y. Wu, C. Wang, S. Liu, D. Tompkins, Z. Chen, and F. Wei, "BEATs: Audio Pre-Training with Acoustic Tokenizers," in *Proc. 40th International Conference on Machine Learning (ICML)*, vol. 202, 2023, pp. 5178–5193.
- [8] W.-N. Hsu, B. Bolte, Y.-H. H. Tsai, K. Lakhotia, R. Salakhutdinov, and A. Mohamed, "HuBERT: Self-Supervised Speech Representation Learning by Masked Prediction of Hidden Units," *IEEE/ACM Transactions on Audio, Speech, and Language Processing*, vol. 29, pp. 3451–3460, 2021, doi: [10.1109/TASLP.2021.3122291](https://doi.org/10.1109/TASLP.2021.3122291).
- [9] A. Baevski, Y. Zhou, A. Mohamed, and M. Auli, "wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 33, 2020, pp. 12449–12460.
- [10] A. Babu, C. Wang, A. Tjandra, K. Lakhotia, Q. Xu, N. Goyal, K. Singh, P. von Platen, Y. Saraf, J. Pino, A. Baevski, A. Conneau, and M. Auli, "XLS-R: Self-supervised Cross-lingual Speech Representation Learning at Scale," in *Proc. Interspeech 2022*, Incheon, Korea, 2022, pp. 2278–2282, doi: [10.21437/Interspeech.2022-143](https://doi.org/10.21437/Interspeech.2022-143).
- [11] J. H. Chowdhury, S. Ramanna, and K. Kotecha, "Speech emotion recognition with light weight deep neural ensemble model using hand crafted features," *Scientific Reports*, vol. 15, no. 1, art. 11824, pp. 1–14, 2025, doi: [10.1038/s41598-025-95734-z](https://doi.org/10.1038/s41598-025-95734-z).
- [12] F. Eyben, K. R. Scherer, B. W. Schuller, J. Sundberg, E. André, C. Busso, L. Y. Devillers, J. Epps, P. Laukka, S. S. Narayanan, and K. P. Truong, "The Geneva Minimalistic Acoustic Parameter Set (GeMAPS) for Voice Research and Affective Computing," *IEEE Transactions on Affective Computing*, vol. 7, no. 2, pp. 190–202, Apr.–Jun. 2016, doi: [10.1109/TAFFC.2015.2457417](https://doi.org/10.1109/TAFFC.2015.2457417).
- [13] B. W. Schuller, A. Batliner, C. Bergler, E.-M. Messner, A. Hamilton, S. Amiriparian, A. Baird, G. Rizos, M. Schmitt, L. Stappen, H. Baumeister, A. D. MacIntyre, and S. Hantke, "The INTERSPEECH 2020 Computational Paralinguistics Challenge: Elderly Emotion, Breathing & Masks," in *Proc. Interspeech 2020*, Shanghai, China, 2020, pp. 2042–2046, doi: [10.21437/Interspeech.2020-32](https://doi.org/10.21437/Interspeech.2020-32).
- [14] N. Wang and D. Yang, "Speech emotion recognition using fine-tuned Wav2vec2.0 and neural controlled differential equations classifier," *PLoS ONE*, vol. 20, no. 2, art. e0318297, pp. 1–13, Feb. 2025, doi: [10.1371/journal.pone.0318297](https://doi.org/10.1371/journal.pone.0318297).
- [15] A. Hashem, M. Arif, and M. Alghamdi, "Speech emotion recognition approaches: A systematic review," *Speech Communication*, vol. 154, art. 102974, pp. 1–29, Oct. 2023, doi: [10.1016/j.specom.2023.102974](https://doi.org/10.1016/j.specom.2023.102974).
- [16] M. B. Akçay and K. Oğuz, "Speech emotion recognition: Emotional models, databases, features, preprocessing methods, supporting modalities, and classifiers," *Speech Communication*, vol. 116, pp. 56–76, Jan. 2020, doi: [10.1016/j.specom.2019.12.001](https://doi.org/10.1016/j.specom.2019.12.001).
- [17] H. Cao, D. G. Cooper, M. K. Keutmann, R. C. Gur, A. Nenkova, and R. Verma, "CREMA-D: Crowd-Sourced Emotional Multimodal Actors Dataset," *IEEE Transactions on Affective Computing*, vol. 5, no. 4, pp. 377–390, Oct.–Dec. 2014, doi: [10.1109/TAFFC.2014.2336244](https://doi.org/10.1109/TAFFC.2014.2336244).
- [18] S. R. Livingstone and F. A. Russo, "The Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS): A dynamic, multimodal set of facial and vocal expressions in North American English," *PLoS ONE*, vol. 13, no. 5, art. e0196391, pp. 1–33, May 2018, doi: [10.1371/journal.pone.0196391](https://doi.org/10.1371/journal.pone.0196391).
- [19] S. Haq and P. J. B. Jackson, "Multimodal Emotion Recognition," in *Machine Audition: Principles, Algorithms and Systems*, W. Wang, Ed., Hershey, PA: IGI Global, 2010, pp. 398–423, doi: [10.4018/978-1-61520-919-4.ch017](https://doi.org/10.4018/978-1-61520-919-4.ch017).
- [20] M. K. Pichora-Fuller and K. Dupuis, "Toronto Emotional Speech Set (TESS)," *Scholars Portal Dataverse*, vol. 1, 2020, doi: [10.5683/SP2/E8H2MF](https://doi.org/10.5683/SP2/E8H2MF).
- [21] A. Goel, M. Hira, and A. Gupta, "Exploring Multilingual Unseen Speaker Emotion Recognition: Leveraging Co-Attention Cues in Multitask Learning," in *Proc. Interspeech 2024*, Kos Island, Greece, 2024, pp. 2340–2344, doi: [10.21437/Interspeech.2024-1820](https://doi.org/10.21437/Interspeech.2024-1820).
- [22] H. Rathnayake, J. James, G. Leoni, A. Nicholas, C. Watson, and P. Keegan, "A review on speech emotion recognition for low-resource and Indigenous languages," *Speech Communication*, vol. 176, art. 103342, pp. 1–25, Jan. 2026, doi: [10.1016/j.specom.2025.103342](https://doi.org/10.1016/j.specom.2025.103342).
- [23] S. T. Alam Monisha and S. Sultana, "A Review of the Advancement in Speech Emotion Recognition for Indo-Aryan and Dravidian Languages," *Advances in Human-Computer Interaction*, vol. 2022, art. 9602429, pp. 1–11, Dec. 2022, doi: [10.1155/2022/9602429](https://doi.org/10.1155/2022/9602429).
- [24] A. Pasad, J.-C. Chou, and K. Livescu, "Layer-wise Analysis of a Self-supervised Speech Representation Model," in *Proc. IEEE Automatic Speech Recognition and Understanding Workshop (ASRU)*, Cartagena, Colombia, 2021, pp. 914–921, doi: [10.1109/ASRU51503.2021.9688093](https://doi.org/10.1109/ASRU51503.2021.9688093).
- [25] J. Wagner, D. Schiller, A. Seiderer, and E. André, "Deep learning in paralinguistic recognition tasks: Are hand-crafted features still relevant?," in *Proc. Interspeech 2018*, Hyderabad, India, 2018, pp. 147–151, doi: [10.21437/Interspeech.2018-1238](https://doi.org/10.21437/Interspeech.2018-1238).
- [26] S. Latif, R. Rana, S. Khalifa, R. Jurdak, J. Qadir, and B. W. Schuller, "Survey of Deep Representation Learning for Speech Emotion Recognition," *IEEE Transactions on Affective Computing*, vol. 14, no. 2, pp. 1634–1654, Apr.–Jun. 2023, doi: [10.1109/TAFFC.2021.3114365](https://doi.org/10.1109/TAFFC.2021.3114365).
- [27] L. Pepino, P. Riera, and L. Ferrer, "Emotion Recognition from Speech Using wav2vec 2.0 Embeddings," in *Proc. Interspeech 2021*, Brno, Czech Republic, 2021, pp. 3400–3404, doi: [10.21437/Interspeech.2021-703](https://doi.org/10.21437/Interspeech.2021-703).
- [28] C. Busso, M. Bulut, C.-C. Lee, A. Kazemzadeh, E. Mower, S. Kim, J. N. Chang, S. Lee, and S. S. Narayanan, "IEMOCAP: Interactive emotional dyadic motion capture database," *Language Resources and Evaluation*, vol. 42, no. 4, pp. 335–359, Dec. 2008, doi: [10.1007/s10579-008-9076-6](https://doi.org/10.1007/s10579-008-9076-6).
- [29] M. Mauch and S. Dixon, "pYIN: A Fundamental Frequency Estimator Using Probabilistic Threshold Distributions," in *Proc. IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)*, Florence, Italy, 2014, pp. 659–663, doi: [10.1109/ICASSP.2014.6853678](https://doi.org/10.1109/ICASSP.2014.6853678).
- [30] C. Sun, Y. Zhou, X. Huang, J. Yang, and X. Hou, "Combining wav2vec 2.0 Fine-Tuning and ConLearnNet for Speech Emotion Recognition," *Electronics*, vol. 13, no. 6, art. 1103, pp. 1–19, Mar. 2024, doi: [10.3390/electronics13061103](https://doi.org/10.3390/electronics13061103).
- [31] Sarthwa8, "Indian TTS Emotion 60min: Speech Emotion Dataset for Indian English and Hindi," Hugging Face Datasets, 2023. [Online]. Available: https://huggingface.co/datasets/sarthwa8/indian-tts-emotion-60min.
- [32] Ghostieee11, "Vaani Speech Corpus: Multilingual Indic Speech Dataset," Hugging Face Datasets, 2023. [Online]. Available: https://huggingface.co/datasets/ghostieee11/vaani-speech-corpus.
- [33] RapidOrc121, "Audio Emotion Detection Dataset," Hugging Face Datasets, 2023. [Online]. Available: https://huggingface.co/datasets/RapidOrc121/audio-emotion-detection-dataset.
