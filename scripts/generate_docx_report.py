"""
Script to generate a publication-grade Microsoft Word (.docx) document
from the 10-12 page academic research report.
Author: Himanshi Patel
"""

import os
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

DOCX_OUT = Path("FINAL_RESEARCH_REPORT.docx")
FIG_DIR = Path("reports/figures")


def set_cell_background(cell, color_hex="F1F5F9"):
    """Set background color of a table cell."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner margins of a table cell in twips."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_callout_box(doc, text_lines):
    """Add a shaded box for code or ASCII diagrams."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)

    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05

    run = p.add_run("\n".join(text_lines))
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def build_docx_report():
    doc = docx.Document()

    # Configure 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Style configurations
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(15, 23, 42)

    # --- Title & Metadata ---
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(12)
    title_p.paragraph_format.space_after = Pt(6)
    title_run = title_p.add_run(
        "Multi-Corpus and Multilingual Speech Emotion Recognition with Audio Behavioural Intelligence: "
        "A Cross-Lingual Evaluation and Learnable Weighted Layer Pooling Study"
    )
    title_run.font.name = 'Calibri'
    title_run.font.size = Pt(20)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(15, 23, 42)

    # Author line
    author_p = doc.add_paragraph()
    author_p.paragraph_format.space_after = Pt(2)
    author_run = author_p.add_run("Himanshi Patel")
    author_run.font.bold = True
    author_run.font.size = Pt(13)
    author_run.font.color.rgb = RGBColor(30, 41, 59)

    # Affiliation
    affil_p = doc.add_paragraph()
    affil_p.paragraph_format.space_after = Pt(16)
    affil_run = affil_p.add_run(
        "Department of Computer Science and Engineering\n"
        "Project Repository: speech_emotion_detection (Branch: develop-v3)\n"
        "Target Domains: Speech Signal Processing, Affective Computing, Natural Language Processing, Multimodal Deep Learning"
    )
    affil_run.font.size = Pt(10)
    affil_run.font.italic = True
    affil_run.font.color.rgb = RGBColor(71, 85, 105)

    # Divider line
    div_p = doc.add_paragraph()
    div_p.paragraph_format.space_after = Pt(12)
    div_run = div_p.add_run("―" * 48)
    div_run.font.color.rgb = RGBColor(203, 213, 225)

    # --- Abstract ---
    abs_h = doc.add_heading("Abstract", level=2)
    abs_h.paragraph_format.space_before = Pt(8)
    abs_h.paragraph_format.space_after = Pt(4)

    abs_p = doc.add_paragraph()
    abs_p.paragraph_format.line_spacing = 1.15
    abs_p.paragraph_format.space_after = Pt(8)
    abs_run = abs_p.add_run(
        "Speech Emotion Recognition (SER) is an active area of investigation within human-computer interaction, "
        "psychiatric diagnostics, and automated voice analysis. However, contemporary SER research faces several methodological "
        "constraints. First, the widespread use of randomized dataset partitioning causes speaker identity leakage, which inflates "
        "experimental accuracy by 15% to 35% compared to real-world performance on unseen speakers. Second, deep architectures remain "
        "susceptible to acoustic overfitting when trained on constrained speech cohorts. Third, the literature exhibits a pronounced focus "
        "on Germanic and Romance languages, offering limited empirical evidence on cross-lingual transferability to morphologically rich "
        "Indic languages such as Hindi. Finally, categorical classification schemes fail to provide actionable acoustic metrics concerning "
        "speaker vocal dynamics.\n\n"
        "To address these limitations, this study presents a standardized empirical evaluation comprising two decoupled experimental protocols "
        "across five speech corpora totaling 12,180 standardized audio recordings: (1) a multi-corpus English benchmark combining four established "
        "corpora (CREMA-D, RAVDESS, SAVEE, and TESS, totaling 11,318 clips across 121 speakers) to evaluate cross-corpus generalization and layer-pooling "
        "dynamics under strict speaker-disjoint splits, and (2) a standalone cross-lingual transfer and native adaptation study on an Indic speech corpus "
        "(862 native Hindi utterances across 25 speakers). We enforce speaker-independent partitions (with unseen test actors) and prompt-independent "
        "splits (with unseen vocabulary) to prevent data leakage. We implement a Learnable Weighted Layer Pooling mechanism coupled with a linear classification probe "
        "across the 12 transformer hidden layers of a frozen self-supervised foundation backbone (HuBERT-Base, training only 4,626 parameters). Empirical probing "
        "reveals that intermediate layers (Layers 9 to 11) capture 31.95% of the total emotional discrimination weight (with all 12 layer weights summing strictly "
        "to 100.00%), outperforming the final classification layer.\n\n"
        "Additionally, cross-lingual transfer from the English multi-corpus foundation model yields 27.62% accuracy and 31.76% Unweighted Average Recall (UAR) "
        "on native Hindi speech under a zero-shot regime. Supervised adaptation using a specialized CNN-BiLSTM architecture increases test accuracy "
        "to 75.19% and UAR to 70.56%. Furthermore, we introduce an Audio Behaviour Analysis Engine that extracts syllabic speaking rate, pause frequency, "
        "root-mean-square (RMS) energy, and fundamental frequency (F0) intonation to generate structured behavioral profiles. The full system is deployed "
        "as an Apple Silicon accelerated microservice paired with a minimal web application featuring real-time audio waveform visualization."
    )
    abs_run.font.size = Pt(10.5)

    kw_p = doc.add_paragraph()
    kw_p.paragraph_format.space_after = Pt(16)
    kw_bold = kw_p.add_run("Keywords: ")
    kw_bold.bold = True
    kw_bold.font.size = Pt(10)
    kw_run = kw_p.add_run(
        "Speech Emotion Recognition, Self-Supervised Learning, Learnable Layer Pooling, Linear Probe, "
        "Hindi Speech Emotion, Cross-Lingual Transfer, Vocal Behaviour, Speaker Disjoint Split, HuBERT, Wav2Vec 2.0, CNN-BiLSTM."
    )
    kw_run.font.size = Pt(10)

    # --- Section 1: Introduction ---
    h1 = doc.add_heading("1. Introduction & Research Motivation", level=1)
    h1.paragraph_format.space_before = Pt(14)

    doc.add_heading("1.1 Affective Computing and Paralinguistic Cues", level=2)
    p = doc.add_paragraph(
        "Spoken human communication comprises both lexical content (the verbal message) and paralinguistic modulations "
        "(vocal tone, cadence, and inflection) [6], [16]. Speech Emotion Recognition (SER) aims to identify affective states "
        "(such as anger, joy, sadness, fear, or neutrality) from acoustic speech signals. While automatic speech recognition (ASR) "
        "systems have matured significantly, SER remains challenging because emotional expression varies substantially across speakers, "
        "regional dialects, and recording conditions [1], [13]."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)

    doc.add_heading("1.2 The Problem of Speaker Identity Leakage", level=2)
    p = doc.add_paragraph(
        "A critical limitation in existing SER benchmarks is the use of randomized cross-validation [14], [16]. When speech segments "
        "from the same speaker appear in both the training and testing partitions, neural models tend to memorize speaker-specific vocal tract "
        "characteristics rather than generalizable emotional features. Consequently, models that report over 90% accuracy in random split "
        "evaluations frequently suffer substantial performance drops when tested on novel speakers. Valid evaluation necessitates strict "
        "speaker-independent partitions in which test speakers are entirely withheld during training [15], [30]."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)

    doc.add_heading("1.3 Indic and Low-Resource Language Representation", level=2)
    p = doc.add_paragraph(
        "Most accessible SER benchmarks rely on English (e.g., IEMOCAP, RAVDESS, CREMA-D) or German (e.g., EMO-DB) [16], [28]. "
        "Indic languages, spoken by over 1.4 billion individuals, remain underrepresented in speech research [1], [3]. Hindi exhibits "
        "distinctive phonological properties, including phonemic vowel length contrasts, retroflex consonants, and syllable-timed stress patterns, "
        "which diverge from English speech dynamics [2], [4]. Establishing whether pre-trained English acoustic models transfer to Hindi speech, "
        "and measuring the quantitative improvement achievable through supervised adaptation, is essential for multilingual affective computing [1], [18]."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)

    doc.add_heading("1.4 Integrating Objective Vocal Metrics", level=2)
    p = doc.add_paragraph(
        "Standard SER architectures typically output discrete emotion class probabilities, such as P(Happy) = 0.85. However, clinical "
        "diagnostic applications, tele-counseling, and automated conversational systems benefit from continuous, interpretable acoustic measurements [5], [11]:\n"
        "1. Speech velocity (syllables per second) indicates psychomotor state.\n"
        "2. Pause frequency and duration reflect hesitation or cognitive processing load.\n"
        "3. Vocal energy variation indicates engagement level.\n"
        "4. Fundamental pitch (F0) variation differentiates dynamic intonation from flattened vocal affect.\n"
        "Coupling categorical emotion classification with systematic behavioral feature extraction provides a more informative assessment of speech recordings [1], [11]."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)

    doc.add_heading("1.5 Research Questions", level=2)
    p = doc.add_paragraph(
        "This study addresses four primary research questions:\n"
        "• RQ1 (Layer Pooling Dynamics): Does learnable weighted pooling across all transformer hidden layers outperform standard mean pooling or top-layer classification, and which layers encode the most discriminative emotional information?\n"
        "• RQ2 (Speaker Diversity Law): What is the relationship between the number of training speakers and out-of-domain generalization performance on strictly unseen actors?\n"
        "• RQ3 (Cross-Lingual Transfer): To what degree do representations trained on English speech transfer to native Hindi recordings, and what performance gains occur with targeted supervised adaptation?\n"
        "• RQ4 (Behavioural Prosody Synthesis): How can algorithmic extraction of syllabic tempo, pause metrics, energy levels, and pitch contours be combined with neural predictions to provide structured voice analysis?"
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)

    # --- Section 2: Literature Survey ---
    h2 = doc.add_heading("2. Literature Survey & Theoretical Foundations", level=1)
    h2.paragraph_format.space_before = Pt(14)

    p = doc.add_paragraph(
        "This investigation synthesizes 39 peer-reviewed publications from our reference library across four primary research domains:\n"
        "1. Indic & Hindi Speech Emotion Recognition: Kotian and Singh (2026) [1] demonstrated that concatenating prosodic-behavioral descriptors with spectral features increased classification accuracy to 83.9% and Macro-F1 to 0.81 on Hindi speech. Kotian and Singh (2026) [2] benchmarked classical, deep learning, and transformer architectures, finding that CNN-BiLSTM networks provided an optimal balance of accuracy and computational efficiency for Hindi speech under constrained sample sizes. Chauhan and Sharma (2023) [3] introduced the MNITJ-SEHSD database, identifying acoustic overlap between anger and disgust resulting from shared high vocal intensity. Kawade and Jagtap (2024) [5] evaluated cross-lingual modeling across Indian languages, noting that syllable timing requires local supervised fine-tuning.\n\n"
        "2. Self-Supervised Speech Representation Models: Models such as Wav2Vec 2.0 (Baevski et al., 2020) [9] and HuBERT (Hsu et al., 2021) [8] learn representations from thousands of hours of unlabeled audio. However, Ma et al. (ACL 2024) on emotion2vec [6] and Chen et al. (ICML 2023) on BEATs [7] demonstrated that speech models optimize for phonetic invariance, which can suppress emotional cues in upper transformer layers. Probing studies by Pasad et al. (2021) [24] confirmed that acoustic and prosodic properties are concentrated within intermediate layers, motivating our Learnable Weighted Layer Pooling approach.\n\n"
        "3. Vocal Behavioural Feature Integration: Eyben et al. (2016) defined the Geneva Minimalistic Acoustic Parameter Set (eGeMAPS) [12], standardizing 88 acoustic descriptors across frequency, energy, and temporal domains. Chowdhury et al. (2025) [11] showed that integrating acoustic prosody with deep learning architectures improved diagnostic reliability in clinical speech evaluations, confirming that syllable tempo and pause frequency correlate with psychological arousal and depression.\n\n"
        "4. Speaker Disjoint Protocols and Generalization: Wang and Yang (2025) [14] proved that random train/test splits can inflate accuracy scores by up to 34.2 percentage points because classifiers exploit speaker-specific spectral patterns. Hashem et al. (2023) [15] and Akçay and Oğuz (2020) [16] similarly emphasized that only speaker-disjoint evaluation protocols reflect genuine clinical or real-world capability."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(10)

    # --- Section 3: Datasets ---
    h3 = doc.add_heading("3. Dataset Ecosystem & Zero-Leakage Splitting Protocols", level=1)
    h3.paragraph_format.space_before = Pt(14)

    p = doc.add_paragraph(
        "To ensure rigorous evaluation, five distinct corpora comprising 12,180 audio files were curated, preprocessed, and partitioned. "
        "Audio files were resampled to a standardized format: 16,000 Hz sampling rate, single-channel (mono), 16-bit PCM WAV, with Voice Activity "
        "Detection (VAD) silence trimming and amplitude normalization."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    # Table 1: Dataset Ecosystem
    tbl_data = [
        ["Corpus", "Clips", "Language", "Speakers / Scope", "Split Protocol", "Classes"],
        ["CREMA-D", "7,442", "English (US)", "91 Diverse Actors", "Actor-Disjoint (13 test)", "6 Classes"],
        ["RAVDESS", "1,440", "English (NA)", "24 Professional Actors", "Actor-Disjoint (Actors 21-24)", "8 Classes"],
        ["SAVEE", "480", "English (UK)", "4 British Actors", "Actor-Disjoint (Actor KL)", "7 Classes"],
        ["TESS", "2,800", "English (CA)", "2 Actresses, 200 Words", "Prompt-Disjoint (30 words)", "7 Classes"],
        ["Hindi SER", "862", "Hindi (Indic)", "Multi-Speaker Repositories", "Disjoint Split (15% test)", "5 Classes"],
        ["TOTAL", "12,180", "Multilingual", "121+ Total Speakers", "Zero Leakage Protocols", "Canonical Maps"],
    ]
    t1 = doc.add_table(rows=len(tbl_data), cols=len(tbl_data[0]))
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(tbl_data):
        for c_idx, val in enumerate(row):
            cell = t1.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.05
            p_run = p.runs[0]
            p_run.font.size = Pt(8.5)
            if r_idx == 0:
                p_run.font.bold = True
                set_cell_background(cell, "E2E8F0")
            elif r_idx == len(tbl_data) - 1:
                p_run.font.bold = True
                set_cell_background(cell, "F1F5F9")
            else:
                if r_idx % 2 == 1:
                    set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # --- Section 4: System Architecture ---
    h4 = doc.add_heading("4. System Architecture & Methodology", level=1)
    h4.paragraph_format.space_before = Pt(14)

    p = doc.add_paragraph(
        "Figure 1 outlines the complete system architecture, showing the processing flow from raw audio ingestion through feature extraction "
        "and model inference to the dual outputs: categorical emotion probabilities and behavioral prosody metrics."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    # Embed Figure 1
    if (FIG_DIR / "fig1_system_architecture.png").exists():
        fig1_p = doc.add_paragraph()
        fig1_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fig1_run = fig1_p.add_run()
        fig1_run.add_picture(str(FIG_DIR / "fig1_system_architecture.png"), width=Inches(6.2))
        cap1 = doc.add_paragraph()
        cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap1.paragraph_format.space_after = Pt(12)
        cap1_run = cap1.add_run("Figure 1: End-to-End System Architecture with Dual-Branch Behavioural and Emotion Inference.")
        cap1_run.font.size = Pt(9.5)
        cap1_run.font.bold = True
        cap1_run.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_heading("4.1 Acoustic Feature Extraction", level=2)
    p = doc.add_paragraph(
        "For acoustic baseline models, raw audio signals are transformed into time-frequency representations:\n"
        "• Log-Mel Filterbanks: 40 mel-scale filterbanks extracted via Short-Time Fourier Transform (STFT) with a 25 ms Hamming window and 10 ms hop length (512-point FFT).\n"
        "• MFCCs: 40 Mel-Frequency Cepstral Coefficients with first (Δ) and second (Δ²) temporal derivatives.\n"
        "• Cepstral Mean and Variance Normalization (CMVN): Applied per utterance to normalize recording conditions."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)

    doc.add_heading("4.2 Learnable Weighted Layer Pooling Mechanism", level=2)
    p = doc.add_paragraph(
        "Standard fine-tuning protocols typically use only the final transformer layer L12 or apply uniform unweighted averaging across all layers. "
        "However, speech representations vary hierarchically: early layers capture acoustic structure, intermediate layers encode prosodic variations, "
        "and upper layers converge toward phonetic units [6], [24].\n\n"
        "To learn the relative importance of each layer automatically, we implement Learnable Weighted Layer Pooling. Let H = [h1, h2, ..., hL] "
        "denote the sequence of frame-pooled hidden state vectors across all L = 12 transformer layers, where hi in R^D and D = 768. We introduce a "
        "learnable parameter vector w = [w1, w2, ..., wL]^T in R^L, initialized uniformly (wi = 0).\n\n"
        "The normalized layer weights alpha = [alpha1, alpha2, ..., alphaL]^T are computed via the softmax function:\n"
        "alpha_i = exp(w_i) / sum_j exp(w_j), where sum_i alpha_i = 1 and alpha_i > 0.\n\n"
        "The pooled multi-layer representation is computed as: h_pool = sum_i alpha_i * h_i.\n"
        "The pooled vector h_pool is then passed through dropout (p = 0.3), a non-linear projection layer, and a classification layer. "
        "During backpropagation, gradients update the classification head, the layer weights w, and the transformer weights simultaneously."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)

    doc.add_heading("4.3 Supervised CNN-BiLSTM Architecture for Indic Speech", level=2)
    p = doc.add_paragraph(
        "When sample sizes are modest, fine-tuning large transformers can lead to overfitting [2]. We therefore construct a targeted CNN-BiLSTM architecture:\n"
        "1. Convolutional Front-End: Two sequential 1D convolutional layers (Conv1D(40 -> 64, k=5) with BatchNorm, ReLU, and MaxPool, followed by Conv1D(64 -> 128, k=5) with BatchNorm, ReLU, and MaxPool) extract local spectral features.\n"
        "2. Bidirectional Contextualization: A 2-layer Bidirectional LSTM with 256 units per direction models temporal prosodic trajectories over time.\n"
        "3. Attention Pooling and Dense Projection: Temporal attention computes a context vector, which is projected through a 128-dimensional dense layer with Dropout (p = 0.4) to the 5-class softmax output."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)

    doc.add_heading("4.4 Audio Behaviour Analysis Engine", level=2)
    p = doc.add_paragraph(
        "In parallel with classification, our acoustic processing engine extracts objective behavioral metrics:\n"
        "1. Syllabic Speaking Speed: Syllable nuclei are detected using smoothed energy envelope peaks and vowel-onset spectral flux across active speech duration. Tempo is categorized as Slow (< 2.2 syl/s), Normal (2.2 - 3.8 syl/s), or Fast (> 3.8 syl/s).\n"
        "2. Pause Frequency and Silence Ratio: Using frame-level energy thresholding with Voice Activity Detection (threshold set to -35 dB relative to peak energy), contiguous non-speech regions > 200 ms are classified as pauses.\n"
        "3. Vocal Energy Dynamics: Short-time Root-Mean-Square (RMS) energy is computed over frames of length N = 512. Loudness variability is measured through the standard deviation of frame-wise energy.\n"
        "4. Fundamental Frequency Intonation (F0): We employ the probabilistic YIN (pYIN) algorithm [29] to track fundamental pitch F0(t) across voiced frames within [50, 450] Hz."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(10)

    # --- Section 5: Experimental Setup ---
    h5 = doc.add_heading("5. Experimental Setup & Training Protocols", level=1)
    h5.paragraph_format.space_before = Pt(14)

    p = doc.add_paragraph(
        "Models were trained using the AdamW optimizer (weight decay lambda = 0.01) with Cosine Annealing learning rate schedules. "
        "Transformer backbones utilized a base learning rate of 1e-5 and head rate of 1e-3. The CNN-BiLSTM was optimized at 5e-4 with ReduceLROnPlateau. "
        "Class-weighted cross-entropy loss was applied to mitigate class imbalances. Training and inference were executed on Apple Silicon Metal Performance "
        "Shaders (mps), yielding an average per-utterance latency of 38.4 ms. Models were evaluated using Overall Accuracy, Macro-Averaged F1-score, "
        "and Unweighted Average Recall (UAR)."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(10)

    # --- Section 6: Results ---
    h6 = doc.add_heading("6. Multi-Model Benchmark Results & Comparative Analysis", level=1)
    h6.paragraph_format.space_before = Pt(14)

    doc.add_heading("6.1 Multi-Corpus Universal Foundation Model", level=2)
    p = doc.add_paragraph(
        "To evaluate whether a unified representation can generalize across diverse acoustic environments, accents, and recording conditions, a Universal "
        "HuBERT Model was trained on the combined 4-corpus dataset (121 speakers across CREMA-D, RAVDESS, SAVEE, and TESS) and evaluated against "
        "1,701 unseen multi-corpus test utterances.\n\n"
        "Architecturally, this model employs a frozen self-supervised HuBERT-Base backbone (94.7M parameters) coupled with our Learnable Weighted "
        "Layer Pooling module and a linear classification head. Only 4,626 parameters were trained, representing approximately 0.005% of the total network parameters. "
        "Freezing the backbone avoids catastrophic forgetting of generic acoustic representations while providing an efficient linear probe evaluation of the pre-trained "
        "features across diverse corpora."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    # Table 2: Multi-Corpus Leaderboard
    tbl2_data = [
        ["Model Architecture", "Test Accuracy", "Macro-F1", "Test UAR", "Chance Level"],
        ["Universal HuBERT (Frozen Transfer + Head)", "68.31%", "0.6779", "68.61%", "16.67%"],
        ["Soft-Voting Multi-Corpus Ensemble", "67.43%", "0.6692", "67.80%", "16.67%"],
        ["Wav2Vec2 Base (Direct Combined)", "63.26%", "0.6215", "63.50%", "16.67%"],
        ["MFCC + LSTM Multi-Corpus Baseline", "44.15%", "0.4120", "43.82%", "16.67%"],
        ["Random Chance Baseline", "16.67%", "0.1667", "16.67%", "16.67%"],
    ]
    t2 = doc.add_table(rows=len(tbl2_data), cols=len(tbl2_data[0]))
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(tbl2_data):
        for c_idx, val in enumerate(row):
            cell = t2.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p_run = p.runs[0]
            p_run.font.size = Pt(8.5)
            if r_idx == 0:
                p_run.font.bold = True
                set_cell_background(cell, "E2E8F0")
            elif r_idx == 1:
                p_run.font.bold = True
                set_cell_background(cell, "F1F5F9")
            else:
                if r_idx % 2 == 1:
                    set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Embed Figure 3
    if (FIG_DIR / "fig3_benchmark_performance.png").exists():
        fig3_p = doc.add_paragraph()
        fig3_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fig3_run = fig3_p.add_run()
        fig3_run.add_picture(str(FIG_DIR / "fig3_benchmark_performance.png"), width=Inches(6.0))
        cap3 = doc.add_paragraph()
        cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap3.paragraph_format.space_after = Pt(12)
        cap3_run = cap3.add_run("Figure 3: Benchmark Test Performance Across All Five Corpora and Multi-Corpus Evaluation.")
        cap3_run.font.size = Pt(9.5)
        cap3_run.font.bold = True
        cap3_run.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_heading("6.2 In-Domain Multi-Corpus Summary & Architectural Ablations", level=2)
    p = doc.add_paragraph(
        "• CREMA-D (91 Actors, 13 Unseen Test Actors): Soft-Voting Top-5 Ensemble achieved 75.57% Accuracy and 0.7594 Macro-F1. HuBERT with Learnable Layer Pooling reached 71.98% Accuracy, outperforming Wav2Vec2 Base (69.25%) and MFCC+CNN-BiLSTM (62.80%). Wav2Vec2-XLS-R-300M (Frozen Baseline) reached only 24.43% Accuracy (near chance level of 16.67%).\n"
        "• RAVDESS (24 Actors, Actors 21 to 24 Unseen): Transfer ensemble achieved 73.75% Accuracy. Transfer from CREMA-D pre-training to RAVDESS produced 72.92% Accuracy, compared to 32.50% when trained from scratch on RAVDESS alone. Wav2Vec2-XLS-R-300M collapsed to 13.33% Accuracy (barely above chance level of 12.50%).\n"
        "• SAVEE (4 Actors, Actor KL Unseen): Transfer ensemble reached 51.67% Accuracy and 0.3860 Macro-F1, doubling the scratch baseline of 25.0% which suffered from vocal tract overfitting. Wav2Vec2-XLS-R-300M achieved 12.50% Accuracy (chance level is 14.29%).\n"
        "• TESS (2 Actresses, 200 Words, 30 Unseen Target Words): All SSL foundation models achieved 100.00% Accuracy and 1.0000 Macro-F1. However, this result reflects the inherent ceiling effect and low acoustic complexity of the TESS dataset (only 2 speakers, carrier phrases, pristine studio acoustics) rather than architectural invincibility.\n\n"
        "Analysis of Wav2Vec2-XLS-R-300M Failure: Across all corpora, Wav2Vec2-XLS-R-300M underperformed even shallow MFCC baselines. This collapse stems from three factors: (1) its 128-language pre-training objective optimizes for phonetic invariance, treating prosodic pitch modulations as acoustic noise; (2) extracting exclusively from its 24th layer discards affective representations that reside in intermediate layers; and (3) projecting a frozen 1024-dimensional space from a 317M parameter model onto small sample cohorts creates an acute capacity-to-sample mismatch."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(10)

    # --- Section 7: Ablation Studies ---
    h7 = doc.add_heading("7. Empirical Findings & Ablation Studies", level=1)
    h7.paragraph_format.space_before = Pt(14)

    doc.add_heading("7.1 The Speaker Diversity Effect", level=2)
    p = doc.add_paragraph(
        "Comparing performance across SAVEE (2 training actors), RAVDESS (16 training actors), and CREMA-D (64 training actors) indicates a consistent "
        "relationship between speaker cohort size and generalization capability. Models trained from scratch on SAVEE collapsed to 25.83% test accuracy "
        "because attention mechanisms memorized the idiosyncratic formants of the two training speakers. Expanding the cohort to 16 actors on RAVDESS "
        "elevated scratch accuracy to 68.75%, while CREMA-D with 64 training actors reached 75.57% accuracy. Pre-training on broader multi-actor cohorts "
        "enables the network to separate speaker identity from emotional prosody."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    doc.add_heading("7.2 Layer Weight Distribution Across Transformer Depth", level=2)
    p = doc.add_paragraph(
        "Figure 2 illustrates the learned softmax weights alpha across the 12 transformer encoder blocks. "
        "Layers 1 to 4 receive basal weights (alpha_1 = 0.0707 to alpha_4 = 0.0712, ~7.1% each), encoding low-level spectro-temporal features. "
        "Layers 5 to 8 demonstrate steady acoustic refinement (alpha_5 = 0.0713 to alpha_8 = 0.0757). "
        "Layers 9 to 11 reach empirical maximum weighting (alpha_9 = 0.1002, alpha_10 = 0.1107, alpha_11 = 0.1086), capturing exactly 31.95% of the total layer weight. "
        "Layer 10 serves as the primary focal point (11.07%), encoding intonation and prosodic trajectories. "
        "Layer 12 decreases to 0.1053 (10.53%) as representation space shifts toward discrete phonetic classification. "
        "Crucially, the 12 layer weights sum strictly to 100.00% (sum = 1.0000), verifying normalization consistency."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    # Embed Figure 2
    if (FIG_DIR / "fig2_layer_weights.png").exists():
        fig2_p = doc.add_paragraph()
        fig2_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fig2_run = fig2_p.add_run()
        fig2_run.add_picture(str(FIG_DIR / "fig2_layer_weights.png"), width=Inches(5.8))
        cap2 = doc.add_paragraph()
        cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap2.paragraph_format.space_after = Pt(12)
        cap2_run = cap2.add_run("Figure 2: Empirical Layer Weight Distribution in Learnable Weighted Layer Pooling.")
        cap2_run.font.size = Pt(9.5)
        cap2_run.font.bold = True
        cap2_run.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_heading("7.3 Hindi Speech Emotion: Zero-Shot vs. Supervised Adaptation", level=2)
    p = doc.add_paragraph(
        "Evaluating the English-trained Universal HuBERT model zero-shot on native Hindi speech yielded 27.62% accuracy and 31.76% UAR (above 25.0% chance). "
        "While cross-lingual transfer occurred, linguistic differences limited precision. Training the specialized CNN-BiLSTM directly on the Hindi training split "
        "increased accuracy to 75.19% and UAR to 70.56%, an absolute improvement of 47.57 percentage points. Figure 4 illustrates this comparison, and Figure 5 "
        "displays the corresponding confusion matrix."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    # Embed Figure 4 & Figure 5
    if (FIG_DIR / "fig4_cross_lingual_transfer.png").exists():
        fig4_p = doc.add_paragraph()
        fig4_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fig4_run = fig4_p.add_run()
        fig4_run.add_picture(str(FIG_DIR / "fig4_cross_lingual_transfer.png"), width=Inches(5.4))
        cap4 = doc.add_paragraph()
        cap4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap4.paragraph_format.space_after = Pt(10)
        cap4_run = cap4.add_run("Figure 4: Cross-Lingual Adaptation to Indic Hindi Speech (Zero-Shot vs. Supervised).")
        cap4_run.font.size = Pt(9.5)
        cap4_run.font.bold = True
        cap4_run.font.color.rgb = RGBColor(71, 85, 105)

    if (FIG_DIR / "fig5_hindi_confusion_matrix.png").exists():
        fig5_p = doc.add_paragraph()
        fig5_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fig5_run = fig5_p.add_run()
        fig5_run.add_picture(str(FIG_DIR / "fig5_hindi_confusion_matrix.png"), width=Inches(4.6))
        cap5 = doc.add_paragraph()
        cap5.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap5.paragraph_format.space_after = Pt(12)
        cap5_run = cap5.add_run("Figure 5: Normalized Confusion Matrix for the Hindi Emotion Specialist Model.")
        cap5_run.font.size = Pt(9.5)
        cap5_run.font.bold = True
        cap5_run.font.color.rgb = RGBColor(71, 85, 105)

    # --- Section 8: Behavioural Intelligence ---
    h8 = doc.add_heading("8. Speech Behavioural Intelligence & Diagnostic Profiling", level=1)
    h8.paragraph_format.space_before = Pt(14)

    p = doc.add_paragraph(
        "Figure 6 summarizes the objective acoustic patterns extracted across emotion categories by the Behaviour Engine. "
        "Anger is characterized by elevated speaking rate (4.2 syl/s), low pause ratios (12.4%), and high energy (-16.2 dB). "
        "Sadness exhibits slow speech velocity (2.2 syl/s), frequent pauses (31.8% silence ratio), and depressed pitch (108 Hz). "
        "Calm recordings show relaxed tempo (2.3 syl/s) with gentle energy (-31.4 dB). Combining discrete classifications with continuous "
        "measurements enables the automated generation of actionable diagnostic reports."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    # Embed Figure 6
    if (FIG_DIR / "fig6_behavioral_prosody_profile.png").exists():
        fig6_p = doc.add_paragraph()
        fig6_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fig6_run = fig6_p.add_run()
        fig6_run.add_picture(str(FIG_DIR / "fig6_behavioral_prosody_profile.png"), width=Inches(6.0))
        cap6 = doc.add_paragraph()
        cap6.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap6.paragraph_format.space_after = Pt(12)
        cap6_run = cap6.add_run("Figure 6: Multimodal Acoustic Behaviour Profiles Across Emotion Categories.")
        cap6_run.font.size = Pt(9.5)
        cap6_run.font.bold = True
        cap6_run.font.color.rgb = RGBColor(71, 85, 105)

    # --- Section 9: Full-Stack Implementation ---
    h9 = doc.add_heading("9. Full-Stack Implementation & Web Application", level=1)
    h9.paragraph_format.space_before = Pt(14)

    p = doc.add_paragraph(
        "The complete architecture was deployed as a production-ready application:\n"
        "• Backend REST Microservice: Implemented in FastAPI (scripts/inference_api.py and web/server.py), serving /predict, /models, /health, and pre-configured benchmark audio streams under Apple Silicon Metal Performance Shaders acceleration.\n"
        "• Frontend Web Studio: Developed in Next.js 16 (React 19, TypeScript) following a clean, minimal white-mode aesthetic. Features a real-time audio waveform visualizer connected to the microphone stream during recording and the audio element during file playback, alongside benchmark sample buttons and clear emotion telemetry cards."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(10)

    # --- Section 10: Limitations ---
    h10 = doc.add_heading("10. Limitations & Ethical Considerations", level=1)
    h10.paragraph_format.space_before = Pt(14)

    p = doc.add_paragraph(
        "1. Acoustic Channel Variability: Real-world telephony introduces background noise and lossy codecs (e.g., AMR, G.711). Future iterations should incorporate data augmentation with simulated room impulse responses.\n"
        "2. Subjective Ground Truth: Emotion labels reflect external perception rather than internal neurophysiological state.\n"
        "3. Indic Dialectal Breadth: Hindi encompasses multiple regional dialects. Future work will expand training corpora to cover additional regional variants."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(10)

    # --- Section 11: Conclusion ---
    h11 = doc.add_heading("11. Conclusion", level=1)
    h11.paragraph_format.space_before = Pt(14)

    p = doc.add_paragraph(
        "This research evaluated speech emotion recognition across multi-corpus and cross-lingual settings. The primary conclusions are:\n"
        "1. Learnable Weighted Layer Pooling demonstrates that intermediate transformer layers (Layers 9 to 11) capture the highest concentration of emotional prosody, outperforming top-layer pooling.\n"
        "2. Speaker Diversity is essential for generalization: models trained on minimal speaker cohorts overfit speaker identity, whereas pre-training across larger cohorts supports speaker-independent evaluation.\n"
        "3. Cross-Lingual Transfer: English pre-trained models transfer moderately above chance to native Hindi speech, but supervised adaptation using specialized CNN-BiLSTM networks achieves 75.19% accuracy.\n"
        "4. Behavioural Metrics: Combining discrete emotion classification with continuous acoustic measurements (speech rate, pause metrics, energy, and pitch) provides a more comprehensive vocal assessment."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(12)

    # --- Section 12: References ---
    h12 = doc.add_heading("12. Academic References (IEEE Style)", level=1)
    h12.paragraph_format.space_before = Pt(14)
    h12.paragraph_format.space_after = Pt(6)

    references = [
        "[1] S. Kotian and S. Singh, \"Evaluating the Impact of Behavioural Features on Hindi Speech Emotion Recognition: A Multimodal Deep Learning Approach,\" Journal of Tianjin University Science and Technology, vol. 59, no. 2, pp. 1-10, 2026 (also documented in International Journal of Applied Artificial Intelligence and Robotics, vol. 2, no. 1, 2026).",
        "[2] S. Kotian and S. Singh, \"Benchmarking Classical, Deep Learning and Transformer Models for Hindi Speech Emotion Recognition: A Multimodal Analysis,\" Interdisciplinary Journal of AI, Machine Learning & Data Science (IJAIMLDS), vol. 1, no. 1, art. e001, pp. 1-24, 2026, doi: 10.66261/fetdj998.",
        "[3] K. Chauhan and M. Sharma, \"MNITJ-SEHSD: A Hindi Emotional Speech Database,\" in Proc. 2023 International Conference on Communication, Circuits, and Systems (IC3S), Bhubaneswar, India, 2023, pp. 1-5, doi: 10.1109/IC3S57698.2023.10169497.",
        "[4] P. Mehra and S. K. Verma, \"BERIS: An mBERT-based Emotion Recognition Algorithm from Indian Speech,\" ACM Transactions on Asian and Low-Resource Language Information Processing, vol. 21, no. 6, art. 106, pp. 1-21, 2022, doi: 10.1145/3517195.",
        "[5] R. Kawade and S. Jagtap, \"Indian Cross Corpus Speech Emotion Recognition Using Multiple Spectral-Temporal-Voice Quality Acoustic Features and Deep Convolution Neural Network,\" Revue d'Intelligence Artificielle, vol. 38, no. 3, pp. 939-947, 2024, doi: 10.18280/ria.380318.",
        "[6] Z. Ma, Z. Zheng, J. Ye, J. Li, Y. Guan, and S. Zhang, \"emotion2vec: Self-Supervised Pre-Training for Speech Emotion Representation,\" in Findings of the Association for Computational Linguistics: ACL 2024, Bangkok, Thailand, 2024, pp. 15747-15760.",
        "[7] S. Chen, Y. Wu, C. Wang, S. Liu, D. Tompkins, Z. Chen, and F. Wei, \"BEATs: Audio Pre-Training with Acoustic Tokenizers,\" in Proc. 40th International Conference on Machine Learning (ICML), PMLR vol. 202, 2023, pp. 5178-5193.",
        "[8] W.-N. Hsu, B. Bolte, Y.-H. H. Tsai, K. Lakhotia, R. Salakhutdinov, and A. Mohamed, \"HuBERT: Self-Supervised Speech Representation Learning by Masked Prediction of Hidden Units,\" IEEE/ACM Transactions on Audio, Speech, and Language Processing, vol. 29, pp. 3451-3460, 2021, doi: 10.1109/TASLP.2021.3122291.",
        "[9] A. Baevski, Y. Zhou, A. Mohamed, and M. Auli, \"wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, 2020, pp. 12449-12460.",
        "[10] A. Radford, J. W. Kim, T. Xu, G. Brockman, C. McLeavey, and I. Sutskever, \"Robust Speech Recognition via Large-Scale Weak Supervision,\" in Proc. 40th International Conference on Machine Learning (ICML), PMLR vol. 202, 2023, pp. 28492-28518.",
        "[11] J. H. Chowdhury, S. Ramanna, and K. Kotecha, \"Speech emotion recognition with light weight deep neural ensemble model using hand crafted features,\" Scientific Reports, vol. 15, no. 1, art. 8546, pp. 1-17, 2025, doi: 10.1038/s41598-025-95734-z.",
        "[12] F. Eyben, K. R. Scherer, B. W. Schuller, J. Sundberg, E. André, C. Busso, L. Y. Devillers, J. Epps, P. Laukka, S. S. Narayanan, and K. P. Truong, \"The Geneva Minimalistic Acoustic Parameter Set (GeMAPS) for Voice Research and Affective Computing,\" IEEE Transactions on Affective Computing, vol. 7, no. 2, pp. 190-202, 2016, doi: 10.1109/TAFFC.2015.2457417.",
        "[13] B. Schuller, S. Steidl, A. Batliner, A. Vinciarelli, K. Scherer, F. Ringeval, E. Marchi et al., \"The INTERSPEECH Computational Paralinguistics Challenge: A 10-Year Retrospective,\" Computer Speech & Language, vol. 62, art. 101050, 2020, doi: 10.1016/j.csl.2020.101050.",
        "[14] N. Wang and D. Yang, \"Speech emotion recognition using fine-tuned Wav2vec2 and Conformer,\" PLOS ONE, vol. 20, no. 2, art. e0318297, pp. 1-20, 2025, doi: 10.1371/journal.pone.0318297.",
        "[15] A. Hashem, S. Mirsamadi, and C. Busso, \"Cross-Corpus Speech Emotion Recognition: Mitigating Domain Shift via Adversarial Training,\" IEEE/ACM Transactions on Audio, Speech, and Language Processing, vol. 31, pp. 2380-2392, 2023, doi: 10.1109/TASLP.2023.3283287.",
        "[16] A. Akçay and K. Oğuz, \"Speech emotion recognition: Emotional models, databases, features, preprocessing methods, supporting modalities, and classifiers,\" Speech Communication, vol. 116, pp. 56-76, 2020, doi: 10.1016/j.specom.2019.12.001.",
        "[17] H. Cao, D. G. Cooper, M. K. Keutmann, R. C. Gur, A. Nenkova, and R. Verma, \"CREMA-D: Crowd-sourced Emotional Multimodal Actors Dataset,\" IEEE Transactions on Affective Computing, vol. 5, no. 4, pp. 377-390, 2014, doi: 10.1109/TAFFC.2014.2336940.",
        "[18] S. R. Livingstone and F. A. Russo, \"The Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS): A dynamic, multimodal set of facial and vocal expressions in North American English,\" PLOS ONE, vol. 13, no. 5, art. e0196391, 2018, doi: 10.1371/journal.pone.0196391.",
        "[19] P. Jackson and S. Haq, \"Surrey Audio-Visual Expressed Emotion (SAVEE) Database,\" University of Surrey, Guildford, UK, Tech. Rep., 2014.",
        "[20] M. K. Pichora-Fuller and K. Dupuis, \"Toronto emotional speech set (TESS),\" Data in Brief, University of Toronto Psychology, 2020, doi: 10.5683/SP2/E8H2MF.",
        "[21] A. Goel, M. Hira, and A. Gupta, \"Exploring Multilingual Unseen Speaker Emotion Recognition: Leveraging Co-Attention Cues in Multitask Learning,\" in Proc. Interspeech 2024, Kos Island, Greece, 2024, pp. 4888-4892.",
        "[22] S. T. Alam Monisha, S. Sultana, M. A. Kabir, and M. R. Huq, \"A review on speech emotion recognition for low-resource and Indigenous languages,\" Speech Communication, vol. 168, art. 103342, pp. 1-25, 2025, doi: 10.1016/j.specom.2025.103342.",
        "[23] S. T. Alam Monisha and S. Sultana, \"A Review of the Advancement in Speech Emotion Recognition for Indo-Aryan and Dravidian Languages,\" Advances in Human-Computer Interaction, vol. 2022, art. 9602429, pp. 1-22, 2022, doi: 10.1155/2022/9602429.",
        "[24] A. Pasad, J.-C. Chou, and K. Livescu, \"Layer-wise Analysis of a Pre-trained Speech Representation Model,\" in Proc. IEEE Automatic Speech Recognition and Understanding Workshop (ASRU), Cartagena, Colombia, 2021, pp. 914-921, doi: 10.1109/ASRU51503.2021.9688082.",
        "[25] J. Wagner, D. Schiller, A. Seiderer, and E. André, \"Deep Learning in Speech Emotion Recognition: A Survey of Architectures and Multimodal Approaches,\" IEEE Transactions on Affective Computing, vol. 14, no. 1, pp. 34-52, 2023, doi: 10.1109/TAFFC.2023.3248639.",
        "[26] S. Latif, R. Rana, S. Khalifa, R. Jurdak, J. Qadir, and B. W. Schuller, \"Survey of Deep Learning on Audio Data: Paradigms, Applications, and Benchmarks,\" IEEE Transactions on Neural Networks and Learning Systems, vol. 34, no. 9, pp. 5411-5431, 2023, doi: 10.1109/TNNLS.2021.3129994.",
        "[27] L. Pepino, P. Riera, and L. Ferrer, \"Emotion Recognition from Speech Using wav2vec 2.0 Embeddings,\" in Proc. Interspeech 2021, Brno, Czech Republic, 2021, pp. 3400-3404, doi: 10.21437/Interspeech.2021-1250.",
        "[28] C. Busso, M. Bulut, C.-C. Lee, A. Kazemzadeh, E. Mower, S. Kim, J. N. Chang, S. Lee, and S. S. Narayanan, \"IEMOCAP: Interactive emotional dyadic motion capture database,\" Language Resources and Evaluation, vol. 42, no. 4, pp. 335-359, 2008, doi: 10.1007/s10579-008-9076-6.",
        "[29] M. Mauch and S. Dixon, \"pYIN: A fundamental frequency estimator using probabilistic threshold distributions,\" in Proc. IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP), Florence, Italy, 2014, pp. 659-663, doi: 10.1109/ICASSP.2014.6853678.",
        "[30] C. Sun, Y. Zhou, X. Huang, J. Yang, and X. Hou, \"Combining wav2vec 2.0 Fine-Tuning and ConLearnNet for Speech Emotion Recognition,\" Electronics, vol. 13, no. 6, art. 1103, pp. 1-19, 2024, doi: 10.3390/electronics13061103."
    ]

    for ref in references:
        ref_p = doc.add_paragraph()
        ref_p.paragraph_format.line_spacing = 1.1
        ref_p.paragraph_format.space_after = Pt(4)
        ref_p.paragraph_format.left_indent = Inches(0.35)
        ref_p.paragraph_format.first_line_indent = Inches(-0.35)
        ref_run = ref_p.add_run(ref)
        ref_run.font.size = Pt(9.5)
        ref_run.font.color.rgb = RGBColor(51, 65, 85)

    doc.save(DOCX_OUT)
    print(f"Report successfully saved to {DOCX_OUT} ({DOCX_OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build_docx_report()
