#!/usr/bin/env python3
"""
Generate Clean, IEEE / Journal Styled Word Document Report (Pure Black & White)
================================================================================
Generates a publication-grade Microsoft Word report (.docx) matching formal LaTeX
article typography and styling conventions:
- Strict academic black-and-white theme (pure black text RGB(0,0,0), zero decorative colors)
- Times New Roman typography throughout
- Intelligent alignment: Left-aligned headings & references, justified body text
- Booktabs table borders (horizontal black lines, zero vertical lines)
- Mathematical equations in native Word OMML (Office Math Markup Language)
- Centered figures and table captions
- 100% grounded in develop-v3 repository code, configs, saved outputs, and verified citations.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import docx
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT_ROOT / "reports" / "figures"
DOCX_OUT = PROJECT_ROOT / "FINAL_RESEARCH_REPORT.docx"
DESKTOP_DOCX = Path("/Users/prarthanapatel/Desktop/Himanshi/FINAL_RESEARCH_REPORT.docx")

# Pure Black & White Palette
BLACK = RGBColor(0, 0, 0)


def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    """Set inner padding for table cells in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for margin_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{margin_name}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_booktabs_borders_bw(table):
    """Apply classic LaTeX booktabs borders: top/bottom thick, header thin, no verticals."""
    tblPr = table._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')

    top = OxmlElement('w:top')
    top.set(qn('w:sz'), '12')  # 1.5 pt
    top.set(qn('w:val'), 'single')
    top.set(qn('w:space'), '0')
    top.set(qn('w:color'), '000000')
    tblBorders.append(top)

    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:sz'), '12')  # 1.5 pt
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:space'), '0')
    bottom.set(qn('w:color'), '000000')
    tblBorders.append(bottom)

    insideH = OxmlElement('w:insideH')
    insideH.set(qn('w:sz'), '4')  # 0.5 pt
    insideH.set(qn('w:val'), 'single')
    insideH.set(qn('w:space'), '0')
    insideH.set(qn('w:color'), '000000')
    tblBorders.append(insideH)

    for border_name in ['left', 'right', 'insideV']:
        node = OxmlElement(f'w:{border_name}')
        node.set(qn('w:val'), 'none')
        tblBorders.append(node)

    tblPr.append(tblBorders)


def add_omml_equation_block(doc, omml_xml: str, eq_num: str = ""):
    """Inserts a display equation with right-aligned equation number using an invisible table."""
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    tblPr = tbl._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for b in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        node = OxmlElement(f'w:{b}')
        node.set(qn('w:val'), 'none')
        tblBorders.append(node)
    tblPr.append(tblBorders)

    c_math = tbl.cell(0, 0)
    c_num = tbl.cell(0, 1)

    c_math.width = Inches(5.8)
    c_num.width = Inches(0.7)

    c_math.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    c_num.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    set_cell_margins(c_math, top=40, bottom=40, left=0, right=0)
    set_cell_margins(c_num, top=40, bottom=40, left=0, right=0)

    p_math = c_math.paragraphs[0]
    p_math.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_math.paragraph_format.space_before = Pt(0)
    p_math.paragraph_format.space_after = Pt(0)

    try:
        math_element = parse_xml(omml_xml.strip())
        p_math._p.append(math_element)
    except Exception as e:
        run_fallback = p_math.add_run(f"[Display Equation {eq_num}]")
        run_fallback.font.name = "Times New Roman"
        run_fallback.font.italic = True
        run_fallback.font.color.rgb = BLACK

    p_num = c_num.paragraphs[0]
    p_num.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_num.paragraph_format.space_before = Pt(0)
    p_num.paragraph_format.space_after = Pt(0)
    if eq_num:
        r_num = p_num.add_run(f"({eq_num})")
        r_num.font.name = "Times New Roman"
        r_num.font.size = Pt(10)
        r_num.font.color.rgb = BLACK

    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build_clean_word_report():
    doc = Document()

    # --- Page Setup: Standard Academic Margins (0.75 in) ---
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.different_first_page_header_footer = True

        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hp.paragraph_format.space_after = Pt(0)
        hrun = hp.add_run("SPEECH EMOTION RECOGNITION BENCHMARK REPORT")
        hrun.font.name = 'Times New Roman'
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = BLACK

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fp.paragraph_format.space_before = Pt(0)
        frun = fp.add_run()
        frun.font.name = 'Times New Roman'
        frun.font.size = Pt(9)
        frun.font.color.rgb = BLACK
        fldSimple = OxmlElement('w:fldSimple')
        fldSimple.set(qn('w:instr'), 'PAGE')
        frun._r.append(fldSimple)

    # --- Title Block ---
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run(
        "Benchmarking Self-Supervised Speech Representations, Learnable Layer Pooling, and Continuous Acoustic Telemetry for Multi-Corpus and Indic Speech Emotion Recognition"
    )
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(17)
    run_title.font.bold = True
    run_title.font.color.rgb = BLACK

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(8)
    run_sub = p_sub.add_run(
        "A Controlled Empirical Evaluation Across CREMA-D, RAVDESS, SAVEE, TESS, and Indic Hindi Speech"
    )
    run_sub.font.name = 'Times New Roman'
    run_sub.font.size = Pt(11)
    run_sub.font.italic = True
    run_sub.font.color.rgb = BLACK

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_before = Pt(0)
    p_meta.paragraph_format.space_after = Pt(4)
    run_meta = p_meta.add_run("Himanshi (Primary Researcher) and Deep Learning Research Team")
    run_meta.font.name = 'Times New Roman'
    run_meta.font.size = Pt(10)
    run_meta.font.bold = True
    run_meta.font.color.rgb = BLACK

    p_affil = doc.add_paragraph()
    p_affil.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_affil.paragraph_format.space_before = Pt(0)
    p_affil.paragraph_format.space_after = Pt(14)
    run_affil = p_affil.add_run(
        "Department of Computer Science and Engineering\n"
        "Project Repository: speech_emotion_detection (Branch: develop-v3)"
    )
    run_affil.font.name = 'Times New Roman'
    run_affil.font.size = Pt(9.5)
    run_affil.font.italic = True
    run_affil.font.color.rgb = BLACK

    # --- Abstract & Keywords Block ---
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.left_indent = Inches(0.35)
    p_abs.paragraph_format.right_indent = Inches(0.35)
    p_abs.paragraph_format.line_spacing = 1.15
    p_abs.paragraph_format.space_before = Pt(0)
    p_abs.paragraph_format.space_after = Pt(4)

    run_abs_tag = p_abs.add_run("Abstract: ")
    run_abs_tag.font.name = "Times New Roman"
    run_abs_tag.font.size = Pt(9.5)
    run_abs_tag.font.bold = True
    run_abs_tag.font.color.rgb = BLACK

    run_abs_body = p_abs.add_run(
        "Speech Emotion Recognition (SER) is an important area within affective computing, conversational systems, and human-computer interaction. "
        "However, contemporary SER research confronts multiple empirical challenges. First, randomized dataset partitioning causes speaker identity leakage, "
        "which paralinguistic literature [21] has demonstrated artificially inflates experimental accuracy by allowing models to memorize familiar speaker "
        "characteristics. Second, deep architectures remain vulnerable to acoustic overfitting when trained on constrained speaker cohorts. Third, the "
        "literature exhibits a pronounced focus on Germanic and Romance languages, offering limited empirical evidence on cross-lingual transferability to "
        "morphologically rich Indic languages such as Hindi. Finally, categorical classification schemes alone fail to provide granular, interpretable "
        "measurements of continuous vocal behaviour.\n\n"
        "To address these challenges, this study presents a standardized empirical evaluation comprising two decoupled experimental protocols across five "
        "speech corpora totaling 12,180 standardized audio recordings: (1) a multi-corpus English benchmark combining four established corpora (CREMA-D, "
        "RAVDESS, SAVEE, and TESS, totaling 11,318 canonical clips across 121 speakers) to evaluate cross-corpus generalization and layer-pooling dynamics, "
        "and (2) a cross-lingual transfer and in-domain adaptation study on an Indic speech corpus (862 standardized Hindi speech utterances across 14 unique speaker IDs "
        "curated from three open-access collections [31]–[33]). Speaker-disjoint evaluation is enforced for CREMA-D, RAVDESS, and SAVEE; TESS is evaluated under "
        "prompt-disjoint conditions on unseen vocabulary; and the Hindi specialist is evaluated on a stratified utterance-level split. Inspired by the lightweight probing "
        "methodology used in the SUPERB benchmark [2], we implement a Learnable Weighted Layer Pooling mechanism coupled with a linear classification probe "
        "across the 12 transformer encoder blocks of a frozen self-supervised foundation backbone (HuBERT-Base, training only 4,626 parameters, ~0.005% of network "
        "capacity). Empirical evaluation reveals that intermediate layers (Layers 9 to 11) receive approximately 31.95% of the learned normalized pooling weight "
        "(31.94% when summing the exported four-decimal rounded values, with unrounded softmax weights summing to 1.0000), indicating that the trained downstream probe "
        "assigned greater weight to intermediate representations under the evaluated protocol.\n\n"
        "Across the 1,701 pooled multi-corpus test clips, a Universal HuBERT probe (initialized from the best CREMA-D HuBERT checkpoint and adapted on the combined "
        "4-corpus dataset) achieves 68.31% aggregate accuracy (0.6779 Macro-F1, 68.61% UAR), outperforming the zero-shot CREMA-D baseline (60.61%) by +7.70 percentage "
        "points, alongside an unweighted corpus-level macro-average of 61.26% Accuracy and 57.54% UAR across the four diverse corpora. Furthermore, zero-shot cross-lingual "
        "evaluation of the English foundation model on the shared canonical subset of Hindi speech yields 27.62% accuracy and 31.76% Unweighted Average Recall "
        "(UAR) against a 25.00% 4-class chance floor. Supervised in-domain adaptation on the full 5-class Hindi space using a specialized CNN-BiLSTM architecture "
        "substantially increases test accuracy to 74.42% (75.19% via ensemble fusion) and UAR to 70.85% (70.56% ensemble) against a 20.00% 5-class chance floor "
        "(+46.80% single-model gain over zero-shot transfer). Finally, an auxiliary Audio Behaviour Analysis Engine extracts "
        "continuous acoustic telemetry (syllabic speaking rate, pause frequency, RMS energy, and fundamental pitch F0) to provide interpretable behavioural profiles "
        "without asserting clinical psychological diagnosis. The complete system is deployed as an Apple Silicon accelerated microservice paired with a web application "
        "featuring real-time audio waveform visualization."
    )
    run_abs_body.font.name = "Times New Roman"
    run_abs_body.font.size = Pt(9.5)
    run_abs_body.font.color.rgb = BLACK

    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_kw.paragraph_format.left_indent = Inches(0.35)
    p_kw.paragraph_format.right_indent = Inches(0.35)
    p_kw.paragraph_format.line_spacing = 1.15
    p_kw.paragraph_format.space_before = Pt(2)
    p_kw.paragraph_format.space_after = Pt(16)

    run_kw_tag = p_kw.add_run("Keywords: ")
    run_kw_tag.font.name = "Times New Roman"
    run_kw_tag.font.size = Pt(9.5)
    run_kw_tag.font.bold = True
    run_kw_tag.font.color.rgb = BLACK

    run_kw_body = p_kw.add_run(
        "Speech Emotion Recognition, Self-Supervised Learning, Learnable Layer Pooling, Linear Probe, "
        "Hindi Speech Emotion, Cross-Lingual Transfer, Vocal Behaviour, Speaker Disjoint Split, HuBERT, Wav2Vec 2.0, CNN-BiLSTM."
    )
    run_kw_body.font.name = "Times New Roman"
    run_kw_body.font.size = Pt(9.5)
    run_kw_body.font.color.rgb = BLACK

    # --- Typography Helpers ---
    def add_sec_heading(title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = BLACK
        return p

    def add_subsec_heading(title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(10.5)
        run.font.bold = True
        run.font.color.rgb = BLACK
        return p

    def add_body_p(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(5)
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)
        run.font.color.rgb = BLACK
        return p

    def add_short_list_item(num_str, title_str, desc_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.line_spacing = 1.12
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2.5)

        run_num = p.add_run(f"{num_str}. ")
        run_num.font.name = "Times New Roman"
        run_num.font.size = Pt(9.5)
        run_num.font.bold = True
        run_num.font.color.rgb = BLACK

        run_title = p.add_run(f"{title_str}: ")
        run_title.font.name = "Times New Roman"
        run_title.font.size = Pt(9.5)
        run_title.font.bold = True
        run_title.font.color.rgb = BLACK

        run_desc = p.add_run(desc_str)
        run_desc.font.name = "Times New Roman"
        run_desc.font.size = Pt(9.5)
        run_desc.font.color.rgb = BLACK
        return p

    def add_bullet_point(tag_bold, text_body, justify=True):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)

        if tag_bold:
            run_tag = p.add_run(f"{tag_bold}: ")
            run_tag.font.name = "Times New Roman"
            run_tag.font.size = Pt(9.5)
            run_tag.font.bold = True
            run_tag.font.color.rgb = BLACK

        run_body = p.add_run(text_body)
        run_body.font.name = "Times New Roman"
        run_body.font.size = Pt(9.5)
        run_body.font.color.rgb = BLACK
        return p

    def add_figure(img_name, caption_text, width_in=5.8):
        img_path = FIG_DIR / img_name
        if img_path.exists():
            fig_p = doc.add_paragraph()
            fig_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            fig_p.paragraph_format.space_before = Pt(8)
            fig_p.paragraph_format.space_after = Pt(3)
            fig_run = fig_p.add_run()
            fig_run.add_picture(str(img_path), width=Inches(width_in))

            cap_p = doc.add_paragraph()
            cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap_p.paragraph_format.space_before = Pt(2)
            cap_p.paragraph_format.space_after = Pt(10)
            cap_p.paragraph_format.left_indent = Inches(0.3)
            cap_p.paragraph_format.right_indent = Inches(0.3)
            cap_run = cap_p.add_run(caption_text)
            cap_run.font.name = "Times New Roman"
            cap_run.font.size = Pt(9)
            cap_run.font.italic = True
            cap_run.font.color.rgb = BLACK

    # --- Section 1: Introduction ---
    add_sec_heading("1. Introduction & Research Motivation")
    add_body_p(
        "Spoken human communication comprises both lexical content (the verbal message) and paralinguistic modulations "
        "(vocal tone, cadence, and inflection) [6], [16]. Speech Emotion Recognition (SER) aims to identify affective states "
        "(such as anger, joy, sadness, fear, or neutrality) from acoustic speech signals. While automatic speech recognition (ASR) "
        "systems have matured significantly, SER remains challenging because emotional expression varies substantially across "
        "speakers, regional dialects, and recording conditions [1], [13]."
    )

    add_subsec_heading("1.1 The Problem of Speaker Identity Leakage")
    add_body_p(
        "A critical limitation in existing SER benchmarks is the use of randomized cross-validation [16], [21]. When speech segments "
        "from the same speaker appear in both the training and testing partitions, neural models tend to memorize speaker-specific vocal tract "
        "characteristics rather than generalizable emotional features. Consequently, models that report over 90% accuracy in random split "
        "evaluations frequently suffer substantial performance drops when tested on novel speakers. Valid evaluation necessitates strict "
        "speaker-independent partitions in which test speakers are entirely withheld during training [15], [21]."
    )

    add_subsec_heading("1.2 Indic and Low-Resource Language Representation")
    add_body_p(
        "Most accessible SER benchmarks rely on English (e.g., IEMOCAP [28], RAVDESS [18], CREMA-D [17], SAVEE [19], TESS [20]) or German (e.g., EMO-DB) [16]. "
        "Indic languages, spoken by over 1.4 billion individuals, remain underrepresented in speech research [1], [3], [22], [23]. Hindi exhibits "
        "distinctive phonological properties, including phonemic vowel length contrasts, retroflex consonants, and syllable-timed stress patterns, "
        "which diverge from English speech dynamics [3], [4], [5]. Establishing whether pre-trained English acoustic models transfer to Hindi speech, "
        "and measuring the quantitative improvement achievable through supervised adaptation, is essential for multilingual affective computing [1], [18], [22]."
    )

    add_subsec_heading("1.3 Interpretable Acoustic Behavioural Telemetry")
    add_body_p(
        "Standard SER architectures typically output discrete emotion class probabilities, such as P(Happy) = 0.85. However, conversational systems, "
        "tele-counseling interfaces, and voice user interfaces benefit from continuous, interpretable acoustic measurements to assess measurable vocal "
        "behaviour without asserting direct clinical psychological diagnoses [5], [11], [12]:"
    )

    add_short_list_item("1", "Speech Velocity (syllables/s)", "Indicates psychomotor tempo and dynamic vocal cadence.")
    add_short_list_item("2", "Pause Frequency and Duration", "Reflects conversational hesitation, processing intervals, and structural fluency.")
    add_short_list_item("3", "Vocal Energy Variation", "Measures acoustic loudness dynamics and vocal projection intensity.")
    add_short_list_item("4", "Fundamental Pitch (F0) Variation", "Quantifies dynamic pitch inflection versus flattened vocal affect.")

    add_body_p(
        "Coupling categorical emotion classification with systematic continuous acoustic telemetry provides a more comprehensive assessment of vocal recordings [1], [11], [25]."
    )

    add_subsec_heading("1.4 Research Questions (RQ)")
    add_body_p("This study addresses four primary research questions:")

    add_bullet_point("• RQ1 (Layer-Wise Representation Dynamics): ", "How are affective vocal representations distributed across the depths of a frozen self-supervised speech transformer, and what relative weighting does learnable layer pooling converge upon when trained on multi-corpus speech?", justify=True)
    add_bullet_point("• RQ2 (Effect of Training Speaker Diversity): ", "What is the empirical association between training cohort speaker diversity and out-of-domain generalization performance on strictly unseen actors, when accounting for simultaneous variations in corpus conditions?", justify=True)
    add_bullet_point("• RQ3 (Cross-Lingual Transfer to Indic Speech): ", "To what degree do English multi-corpus representations transfer zero-shot to Hindi speech, and what quantitative performance gain is achieved via supervised in-domain adaptation?", justify=True)
    add_bullet_point("• RQ4 (Acoustic Behavioural Profiling): ", "What distinctive continuous acoustic profiles (syllabic speed, pause ratio, vocal energy, and fundamental pitch F0) characterize categorical emotion predictions, and how can auxiliary telemetry complement discrete classification without claiming clinical diagnostic validity?", justify=True)

    # --- Section 2: Literature Survey ---
    add_sec_heading("2. Related Work & Literature Survey")
    add_body_p(
        "This investigation synthesizes 30 scholarly sources across four core theoretical domains:"
    )

    add_subsec_heading("2.1 Indic and Hindi Speech Emotion Recognition")
    add_body_p(
        "Early speech emotion recognition research in India relied predominantly on small private datasets evaluated with conventional "
        "classifiers such as Support Vector Machines (SVM) and Multi-Layer Perceptrons [4], [16]. Kotian and Singh (2026) [1] demonstrated "
        "that combining prosodic-behavioral descriptors (speaking rate, pitch perturbation, pause ratio, and energy dynamics) with acoustic "
        "representations enhanced classification accuracy and macro-F1 on Hindi speech under challenging acoustic conditions. Chauhan, Sharma, and "
        "Varma (2023) [3] introduced the MNITJ-SEHSD database, standardizing an Indic emotion corpus and highlighting acoustic overlap "
        "between anger and disgust resulting from shared high vocal intensity. Kawade and Jagtap (2024) [5] evaluated cross-lingual acoustic modeling "
        "across Indian speech corpora, demonstrating the effectiveness of combining multiple spectral, temporal, and voice quality descriptors with deep "
        "convolutional neural networks. Rathnayake et al. (2026) [22] and Alam Monisha and Sultana (2022) [23] provided comprehensive surveys on the unique "
        "acoustic-phonetic challenges and database resources in low-resource Indo-Aryan and Dravidian speech emotion recognition."
    )

    add_subsec_heading("2.2 Self-Supervised Speech Representation Learning & Probing")
    add_body_p(
        "Self-supervised learning has established powerful representations for speech tasks. Models such as Wav2Vec 2.0 (Baevski et al., 2020) [9] "
        "and HuBERT (Hsu et al., 2021) [8] learn representations from thousands of hours of unlabeled audio through contrastive loss or masked cluster prediction. "
        "Yang et al. (2021) [2] introduced the SUPERB benchmark, establishing standard evaluation methodologies for speech representation learning and demonstrating "
        "that learnable layer-weighted combinations of intermediate representations consistently outperform fixed top-layer embeddings across diverse speech classification tasks. "
        "Pepino, Riera, and Ferrer (2021) [27] and Sun et al. (2024) [30] demonstrated the efficacy of fine-tuning pre-trained representations for downstream "
        "emotion recognition, while Wang and Yang (2025) [14] integrated fine-tuned Wav2vec 2.0 with neural controlled differential equation classifiers. "
        "Recent investigations into speech representation learning (such as emotion2vec [6] and BEATs [7]) further indicate that different speech tasks rely on distinct "
        "representational abstractions across model depth. Probing studies by Pasad, Chou, and Livescu (2021) [24] demonstrated that different acoustic and "
        "linguistic information is distributed non-uniformly across self-supervised speech-representation layers, motivating layer-wise probing rather than relying "
        "exclusively on the final representation. These findings motivate the Learnable Weighted Layer Pooling approach used in this work."
    )

    add_subsec_heading("2.3 Vocal Behavioural Feature Integration")
    add_body_p(
        "Standardized acoustic parameter sets have long provided interpretable metrics for speech analysis. Eyben et al. (2016) defined the Geneva "
        "Minimalistic Acoustic Parameter Set (GeMAPS) and extended GeMAPS (eGeMAPS) [12], standardizing 88 acoustic descriptors across frequency, energy, and temporal domains. "
        "Chowdhury, Ramanna, and Kotecha (2025) [11] showed that integrating hand-crafted acoustic prosody with lightweight deep neural ensemble architectures "
        "improved interpretability and performance across multiple SER benchmarks."
    )

    add_subsec_heading("2.4 Speaker Disjoint Protocols and Generalization")
    add_body_p(
        "Goel, Hira, and Gupta (2024) [21] examined the challenge of unseen speaker generalization in SER, evaluating pretrained speech encoders "
        "(HuBERT, Wav2Vec 2.0, WavLM) under leave-speaker-out multilingual conditions and demonstrating that standard random train/test splits "
        "cause neural models to overfit speaker identity rather than true affective cues. Whereas Goel et al. focused on multi-task co-attention, "
        "the present investigation evaluates a unified multi-corpus English benchmark under canonicalized emotion mappings, analyzes layer-wise pooling "
        "weights, and quantifies both zero-shot cross-lingual transfer and supervised in-domain adaptation on Hindi speech. Hashem, Arif, and Alghamdi (2023) [15] "
        "and Akçay and Oğuz (2020) [16] conducted systematic reviews detailing how cross-corpus evaluation protocols reveal severe performance degradation "
        "when models encounter novel recording environments. Wagner et al. (2018) [25] empirically evaluated hand-crafted features versus learned representations "
        "across paralinguistic tasks, finding that acoustic descriptors provide vital complementarity to deep representations, while Latif et al. (2023) [26] "
        "surveyed deep representation learning paradigms for disentangling speaker identity from affective prosody."
    )

    # --- Section 3: Dataset Ecosystem ---
    add_sec_heading("3. Dataset Ecosystem & Partitioning Protocols")
    add_body_p(
        "To ensure rigorous evaluation, five distinct corpora comprising 12,180 standardized audio files were curated, preprocessed, and partitioned. "
        "Audio files were resampled and standardized to 16,000 Hz sampling rate, single-channel (mono), 16-bit PCM WAV format. Table 1 summarizes the dataset ecosystem."
    )

    add_subsec_heading("3.1 Multi-Corpus English Canonical Standardization")
    add_body_p(
        "The English multi-corpus benchmark incorporates four established speech emotion repositories: CREMA-D [17] (7,442 utterances, 91 actors), "
        "RAVDESS [18] (1,440 utterances, 24 actors), SAVEE [19] (480 utterances, 4 actors), and TESS [20] (2,800 utterances, 2 actresses). Across these four "
        "datasets, raw clips total 12,162. To establish an aligned label space, emotions are mapped to a 6-class canonical ontology: neutral, happy, sad, "
        "angry, fear, and disgust. Non-shared emotions (such as calm and surprise in RAVDESS and SAVEE, totaling 844 clips) were excluded prior to model training, "
        "yielding a standardized multi-corpus pool of 11,318 audio clips from 121 speakers."
    )

    add_subsec_heading("3.2 Indic Hindi Dataset Provenance & Partitioning Protocol")
    add_body_p(
        "The Hindi evaluation utilizes 862 standardized speech utterances (1.80 hours total) curated from three open-access Indic speech repositories [31]–[33]: "
        "(1) Indian TTS Emotion Corpus (sarthwa8/indian-tts-emotion-60min on HuggingFace [31], licensed under CC BY 4.0, contributing 130 clips across 8 speaker IDs "
        "hi_spk01 through hi_spk08); (2) Project Vaani Indian Speech Corpus (ghostieee11/vaani-speech-corpus on HuggingFace [32], contributing 465 standardized segments "
        "derived from the Hindi subset under speaker ID hi_kahanisuno, with dataset card license listed as 'other'); and (3) RapidOrc Audio Emotion Detection Dataset "
        "(RapidOrc121/audio-emotion-detection-dataset on HuggingFace [33], licensed under CC BY 4.0, contributing 267 clips across 5 speaker IDs rapidorc_spk_0 "
        "through rapidorc_spk_4). Across all three source collections, the combined Hindi corpus contains 14 unique speaker IDs spanning five discrete emotion "
        "classes: neutral (363 clips), calm (160 clips), sad (158 clips), angry (105 clips), and happy (76 clips).\n\n"
        "The Hindi corpus was partitioned using an utterance-level stratified split (stratified by emotion class): 604 training clips (70.1%), "
        "129 validation clips (15.0%), and 129 test clips (15.0%). In contrast to the speaker-disjoint splits of CREMA-D, RAVDESS, and SAVEE, "
        "utterances from the 14 Hindi speakers appear across train, validation, and test partitions, reflecting an utterance-level evaluation protocol. "
        "Table 2 documents the exact source provenance and speaker distribution."
    )

    # Table 1: Dataset Ecosystem
    p_cap1 = doc.add_paragraph()
    p_cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap1.paragraph_format.space_before = Pt(8)
    p_cap1.paragraph_format.space_after = Pt(2)
    p_cap1_run = p_cap1.add_run("Table 1: Standardized Dataset Ecosystem and Partitioning Specifications")
    p_cap1_run.font.name = "Times New Roman"
    p_cap1_run.font.size = Pt(9.5)
    p_cap1_run.font.bold = True
    p_cap1_run.font.color.rgb = BLACK

    tbl1_data = [
        ["Corpus", "Utterances", "Language", "Speakers / Scope", "Split Protocol", "Classes"],
        ["CREMA-D", "7,442", "English (US)", "91 Diverse Actors", "Actor-Disjoint (13 Unseen Actors)", "6 Canonical Classes"],
        ["RAVDESS", "1,440", "English (NA)", "24 Professional Actors", "Actor-Disjoint (4 Unseen Actors)", "8 Classes (6 Shared)"],
        ["SAVEE", "480", "English (UK)", "4 British Actors", "Actor-Disjoint (Actor KL Unseen)", "7 Classes (6 Shared)"],
        ["TESS", "2,800", "English (CA)", "2 Actresses, 200 Words", "Prompt-Disjoint (30 Unseen Words)", "7 Classes (6 Shared)"],
        ["Hindi SER", "862", "Hindi (Indic)", "14 Unique Speaker IDs", "Stratified Split (604/129/129)", "5 Discrete Classes"],
        ["Total Evaluated", "12,180", "Multilingual", "135 Total Speakers", "Multi-Corpus Benchmark", "Unified Ontologies"],
    ]
    t1 = doc.add_table(rows=len(tbl1_data), cols=len(tbl1_data[0]))
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_booktabs_borders_bw(t1)
    for r_idx, row in enumerate(tbl1_data):
        for c_idx, val in enumerate(row):
            cell = t1.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if c_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

            p_run = p.runs[0]
            p_run.font.name = "Times New Roman"
            p_run.font.size = Pt(8.5)
            p_run.font.color.rgb = BLACK
            if r_idx == 0 or r_idx == len(tbl1_data) - 1:
                p_run.font.bold = True
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)

    p_t1_note = doc.add_paragraph()
    p_t1_note.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_t1_note.paragraph_format.space_before = Pt(2)
    p_t1_note.paragraph_format.space_after = Pt(6)
    run_t1_note = p_t1_note.add_run(
        "*Note: Across the four English source corpora, raw clips total 12,162 (CREMA-D: 7,442; RAVDESS: 1,440; SAVEE: 480; TESS: 2,800). "
        "Standardizing onto the 6 shared canonical classes (neutral, happy, sad, angry, fear, disgust) excludes 844 non-shared clips (calm and surprise), "
        "yielding 11,318 English clips. Combined with the 862 standardized Hindi clips (5 classes), the complete evaluation encompasses 12,180 audio clips."
    )
    run_t1_note.font.name = "Times New Roman"
    run_t1_note.font.size = Pt(8.0)
    run_t1_note.font.italic = True
    run_t1_note.font.color.rgb = BLACK

    # Table 2: Provenance Table for Hindi
    p_cap_hi = doc.add_paragraph()
    p_cap_hi.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap_hi.paragraph_format.space_before = Pt(8)
    p_cap_hi.paragraph_format.space_after = Pt(2)
    p_cap_hi_run = p_cap_hi.add_run("Table 2: Provenance and Speaker Distribution of Indic Hindi Speech Emotion Corpus")
    p_cap_hi_run.font.name = "Times New Roman"
    p_cap_hi_run.font.size = Pt(9.5)
    p_cap_hi_run.font.bold = True
    p_cap_hi_run.font.color.rgb = BLACK

    tbl_hi_data = [
        ["Source Collection", "Repository Identifier / Source", "Segments", "Speaker IDs", "Emotions Covered", "Licensing / Provenance"],
        ["Indian TTS Emotion", "sarthwa8/indian-tts-emotion-60min", "130", "8 (hi_spk01-08)", "Neutral, Happy, Sad, Angry, Calm", "CC BY 4.0 (Open Access) [31]"],
        ["Project Vaani Subset", "ghostieee11/vaani-speech-corpus", "465", "1 (hi_kahanisuno)", "Neutral, Calm, Sad", "Open Scholarly Access (license: 'other') [32]"],
        ["RapidOrc Emotion", "RapidOrc121/audio-emotion-detection-dataset", "267", "5 (rapidorc_spk_0-4)", "Neutral, Happy, Sad, Angry", "CC BY 4.0 (Open Access) [33]"],
        ["Integrated Hindi Pool", "data/hindi/ (develop-v3)", "862", "14 Unique Speaker IDs", "5 Canonical Discrete Classes", "Stratified Partition (604/129/129)"],
    ]
    t_hi = doc.add_table(rows=len(tbl_hi_data), cols=len(tbl_hi_data[0]))
    t_hi.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_booktabs_borders_bw(t_hi)
    for r_idx, row in enumerate(tbl_hi_data):
        for c_idx, val in enumerate(row):
            cell = t_hi.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if c_idx in [2, 3]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

            p_run = p.runs[0]
            p_run.font.name = "Times New Roman"
            p_run.font.size = Pt(8.5)
            p_run.font.color.rgb = BLACK
            if r_idx == 0 or r_idx == len(tbl_hi_data) - 1:
                p_run.font.bold = True
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)

    p_thi_note = doc.add_paragraph()
    p_thi_note.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_thi_note.paragraph_format.space_before = Pt(2)
    p_thi_note.paragraph_format.space_after = Pt(6)
    run_thi_note = p_thi_note.add_run("*Note: For Project Vaani, 465 represents the count of standardized audio segments derived from the Hindi subset of the source corpus. Speaker counts reflect distinct speaker IDs identified in source metadata.")
    run_thi_note.font.name = "Times New Roman"
    run_thi_note.font.size = Pt(8.0)
    run_thi_note.font.italic = True
    run_thi_note.font.color.rgb = BLACK

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # --- Section 4: Methodology ---
    add_sec_heading("4. Methodology & Model Architecture")
    add_body_p(
        "The system architecture features a dual-branch processing pipeline: (1) a Neural Acoustic Classifier Branch processing audio "
        "through pre-trained self-supervised transformer backbones with learnable weighted layer pooling or CNN-BiLSTM networks, and "
        "(2) an Audio Behaviour Analysis Engine extracting continuous prosodic and temporal dynamics (F0 intonation, syllabic tempo, pause frequency, and RMS loudness)."
    )

    add_figure("fig1_system_architecture.png", "Figure 1: End-to-End System Architecture with Dual-Branch Neural SER and Acoustic Behaviour Analysis.", width_in=6.0)

    add_subsec_heading("4.1 Learnable Weighted Layer Pooling & Linear Probing")
    add_body_p(
        "Inspired by the lightweight probing methodology used in the SUPERB benchmark (Yang et al., 2021) [2] and Pepino et al. (2021) [27], "
        "we adopt a learnable layer-wise weighted sum across all L = 12 transformer encoder representations. In accordance with standard HuggingFace "
        "transformer interfaces, outputs.hidden_states returns 13 tensors (Layer 0 feature projection followed by 12 transformer encoder blocks). "
        "The pooling module explicitly selects the last 12 tensors (hidden_states[-12:]), pooling the outputs of transformer encoder blocks 1 through 12 "
        "(l in {1, ..., 12}) and cleanly excluding the initial CNN feature projection. The Universal HuBERT model is initialized from the best CREMA-D-trained "
        "HuBERT checkpoint (outputs/cremad/hubert/checkpoints/best_model/model.pt, logged as HuBERT (Transfer from CREMAD)) and subsequently adapted on the "
        "combined 4-corpus training set with frozen backbone weights:"
    )

    # Equation 1: Learnable Weighted Layer Pooling
    omml_eq1 = '''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <m:oMath>
        <m:sSub>
          <m:e><m:r><m:rPr><m:sty m:val="b"/></m:rPr><m:t>e</m:t></m:r></m:e>
          <m:sub><m:r><m:t>t</m:t></m:r></m:sub>
        </m:sSub>
        <m:r><m:t> = </m:t></m:r>
        <m:nary>
          <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/></m:naryPr>
          <m:sub><m:r><m:t>l=1</m:t></m:r></m:sub>
          <m:sup><m:r><m:t>L</m:t></m:r></m:sup>
          <m:e>
            <m:sSub>
              <m:e><m:r><m:t>α</m:t></m:r></m:e>
              <m:sub><m:r><m:t>l</m:t></m:r></m:sub>
            </m:sSub>
            <m:sSubSup>
              <m:e><m:r><m:rPr><m:sty m:val="b"/></m:rPr><m:t>h</m:t></m:r></m:e>
              <m:sub><m:r><m:t>t</m:t></m:r></m:sub>
              <m:sup><m:r><m:t>(l)</m:t></m:r></m:sup>
            </m:sSubSup>
          </m:e>
        </m:nary>
        <m:r><m:t>,   where   </m:t></m:r>
        <m:sSub>
          <m:e><m:r><m:t>α</m:t></m:r></m:e>
          <m:sub><m:r><m:t>l</m:t></m:r></m:sub>
        </m:sSub>
        <m:r><m:t> = </m:t></m:r>
        <m:f>
          <m:num>
            <m:r><m:t>exp(</m:t></m:r>
            <m:sSub><m:e><m:r><m:t>w</m:t></m:r></m:e><m:sub><m:r><m:t>l</m:t></m:r></m:sub></m:sSub>
            <m:r><m:t>)</m:t></m:r>
          </m:num>
          <m:den>
            <m:nary>
              <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/></m:naryPr>
              <m:sub><m:r><m:t>j=1</m:t></m:r></m:sub>
              <m:sup><m:r><m:t>L</m:t></m:r></m:sup>
              <m:e>
                <m:r><m:t>exp(</m:t></m:r>
                <m:sSub><m:e><m:r><m:t>w</m:t></m:r></m:e><m:sub><m:r><m:t>j</m:t></m:r></m:sub></m:sSub>
                <m:r><m:t>)</m:t></m:r>
              </m:e>
            </m:nary>
          </m:den>
        </m:f>
      </m:oMath>
    </m:oMathPara>
    '''
    add_omml_equation_block(doc, omml_eq1, "1")

    add_body_p(
        "Here, w in R^L is a learnable parameter vector initialized uniformly (w_l = 0), and alpha in R^L represents the normalized layer weighting. "
        "After computing the layer-weighted sequence e_t, masked temporal mean pooling is applied over valid audio frames:"
    )

    # Equation 2: Masked Temporal Mean Pooling
    omml_eq2 = '''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <m:oMath>
        <m:r><m:rPr><m:sty m:val="b"/></m:rPr><m:t>z</m:t></m:r>
        <m:r><m:t> = </m:t></m:r>
        <m:f>
          <m:num><m:r><m:t>1</m:t></m:r></m:num>
          <m:den>
            <m:nary>
              <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/></m:naryPr>
              <m:sub><m:r><m:t>t=1</m:t></m:r></m:sub>
              <m:sup><m:r><m:t>T</m:t></m:r></m:sup>
              <m:e>
                <m:sSub>
                  <m:e><m:r><m:t>m</m:t></m:r></m:e>
                  <m:sub><m:r><m:t>t</m:t></m:r></m:sub>
                </m:sSub>
              </m:e>
            </m:nary>
          </m:den>
        </m:f>
        <m:nary>
          <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/></m:naryPr>
          <m:sub><m:r><m:t>t=1</m:t></m:r></m:sub>
          <m:sup><m:r><m:t>T</m:t></m:r></m:sup>
          <m:e>
            <m:sSub>
              <m:e><m:r><m:t>m</m:t></m:r></m:e>
              <m:sub><m:r><m:t>t</m:t></m:r></m:sub>
            </m:sSub>
            <m:sSub>
              <m:e><m:r><m:rPr><m:sty m:val="b"/></m:rPr><m:t>e</m:t></m:r></m:e>
              <m:sub><m:r><m:t>t</m:t></m:r></m:sub>
            </m:sSub>
          </m:e>
        </m:nary>
        <m:r><m:t> ∈ </m:t></m:r>
        <m:sSup>
          <m:e><m:r><m:t>ℝ</m:t></m:r></m:e>
          <m:sup><m:r><m:t>D</m:t></m:r></m:sup>
        </m:sSup>
      </m:oMath>
    </m:oMathPara>
    '''
    add_omml_equation_block(doc, omml_eq2, "2")

    add_body_p(
        "where m_t in {0, 1} denotes the attention mask indicating valid audio frames. "
        "The resulting pooled representation z in R^D (D = 768) is projected through a linear classification probe:"
    )

    # Equation 3: Linear Classification Probe
    omml_eq3 = '''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <m:oMath>
        <m:acc>
          <m:accPr><m:chr m:val="^"/></m:accPr>
          <m:e><m:r><m:rPr><m:sty m:val="b"/></m:rPr><m:t>y</m:t></m:r></m:e>
        </m:acc>
        <m:r><m:t> = Softmax</m:t></m:r>
        <m:d>
          <m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr>
          <m:e>
            <m:sSub>
              <m:e><m:r><m:rPr><m:sty m:val="b"/></m:rPr><m:t>W</m:t></m:r></m:e>
              <m:sub><m:r><m:t>c</m:t></m:r></m:sub>
            </m:sSub>
            <m:r><m:rPr><m:sty m:val="b"/></m:rPr><m:t>z</m:t></m:r>
            <m:r><m:t> + </m:t></m:r>
            <m:sSub>
              <m:e><m:r><m:rPr><m:sty m:val="b"/></m:rPr><m:t>b</m:t></m:r></m:e>
              <m:sub><m:r><m:t>c</m:t></m:r></m:sub>
            </m:sSub>
          </m:e>
        </m:d>
      </m:oMath>
    </m:oMathPara>
    '''
    add_omml_equation_block(doc, omml_eq3, "3")

    add_body_p(
        "where W_c in R^(C x D) and b_c in R^C (with C = 6 canonical emotion classes). "
        "Crucially, the 94.7M parameter transformer backbone remains strictly frozen and receives zero gradient updates during training. "
        "Gradients flow exclusively through the 12 scalar layer pooling weights and the linear classification probe: "
        "12 + (768 x 6) + 6 = 4,626 trainable parameters, representing approximately 0.005% of the total network capacity."
    )

    add_subsec_heading("4.2 Supervised CNN-BiLSTM Hindi Specialist Architecture")
    add_body_p(
        "For supervised adaptation to Hindi speech, we deploy a specialized lightweight CNN-BiLSTM network operating on 40-dimensional Mel-Frequency "
        "Cepstral Coefficients (MFCCs) extracted with a 32-ms FFT analysis window (512 samples) and a 10-ms hop size (160 samples) at 16 kHz. "
        "The network architecture comprises: (1) a 3-layer 1D Convolutional frontend (Conv1D-64, Conv1D-128, and Conv1D-256 with kernel size 3, "
        "padding 1, ReLU activations, and BatchNorm1d) to extract local spectro-temporal features; (2) a 2-layer Bidirectional LSTM (hidden size 128 "
        "per direction, yielding 256 output dimensions, with recurrent dropout p = 0.3) to capture bidirectional contextual prosody; (3) a masked "
        "temporal mean pooling layer across speech frames; and (4) a linear classification probe with Dropout(0.3) projecting onto the 5 Hindi emotion "
        "classes. The model contains exactly 923,717 trainable parameters (~924K), all trained end-to-end directly on the Hindi training partition."
    )

    add_subsec_heading("4.3 Audio Behaviour Engine Telemetry")
    add_body_p(
        "The Behaviour Engine calculates four continuous acoustic descriptors: (1) Syllabic Speaking Speed (R_speech = N_syl / T_active in syllables/second), "
        "(2) Pause Frequency and Silence Ratio (P_ratio = T_silence / T_total * 100%), (3) Vocal Energy Dynamics (RMS_dB = 20 * log10(RMS_t + eps)), and "
        "(4) Fundamental Frequency Intonation (F0) computed via the probabilistic YIN (pYIN) algorithm [29]."
    )

    # Equation 4: Syllabic Speaking Rate & Pause Ratio
    omml_eq4 = '''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <m:oMath>
        <m:sSub>
          <m:e><m:r><m:t>R</m:t></m:r></m:e>
          <m:sub><m:r><m:t>speech</m:t></m:r></m:sub>
        </m:sSub>
        <m:r><m:t> = </m:t></m:r>
        <m:f>
          <m:num><m:sSub><m:e><m:r><m:t>N</m:t></m:r></m:e><m:sub><m:r><m:t>syl</m:t></m:r></m:sub></m:sSub></m:num>
          <m:den><m:sSub><m:e><m:r><m:t>T</m:t></m:r></m:e><m:sub><m:r><m:t>active</m:t></m:r></m:sub></m:sSub></m:den>
        </m:f>
        <m:r><m:t>  (syl/s),    </m:t></m:r>
        <m:sSub>
          <m:e><m:r><m:t>P</m:t></m:r></m:e>
          <m:sub><m:r><m:t>ratio</m:t></m:r></m:sub>
        </m:sSub>
        <m:r><m:t> = </m:t></m:r>
        <m:f>
          <m:num><m:sSub><m:e><m:r><m:t>T</m:t></m:r></m:e><m:sub><m:r><m:t>silence</m:t></m:r></m:sub></m:sSub></m:num>
          <m:den><m:sSub><m:e><m:r><m:t>T</m:t></m:r></m:e><m:sub><m:r><m:t>total</m:t></m:r></m:sub></m:sSub></m:den>
        </m:f>
        <m:r><m:t> × 100%</m:t></m:r>
      </m:oMath>
    </m:oMathPara>
    '''
    add_omml_equation_block(doc, omml_eq4, "4")

    # Equation 5: RMS Energy & Pitch Intonation
    omml_eq5 = '''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <m:oMath>
        <m:sSub>
          <m:e><m:r><m:t>RMS</m:t></m:r></m:e>
          <m:sub><m:r><m:t>dB</m:t></m:r></m:sub>
        </m:sSub>
        <m:r><m:t> = 20 </m:t></m:r>
        <m:sSub>
          <m:e><m:r><m:t>log</m:t></m:r></m:e>
          <m:sub><m:r><m:t>10</m:t></m:r></m:sub>
        </m:sSub>
        <m:d>
          <m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr>
          <m:e>
            <m:sSub>
              <m:e><m:r><m:t>RMS</m:t></m:r></m:e>
              <m:sub><m:r><m:t>t</m:t></m:r></m:sub>
            </m:sSub>
            <m:r><m:t> + ε</m:t></m:r>
          </m:e>
        </m:d>
        <m:r><m:t>,    </m:t></m:r>
        <m:sSub>
          <m:e><m:r><m:t>σ</m:t></m:r></m:e>
          <m:sub><m:sSub><m:e><m:r><m:t>F</m:t></m:r></m:e><m:sub><m:r><m:t>0</m:t></m:r></m:sub></m:sSub></m:sub>
        </m:sSub>
        <m:r><m:t> = </m:t></m:r>
        <m:rad>
          <m:radPr><m:degHide m:val="1"/></m:radPr>
          <m:deg/>
          <m:e>
            <m:f>
              <m:num><m:r><m:t>1</m:t></m:r></m:num>
              <m:den><m:r><m:t>M</m:t></m:r></m:den>
            </m:f>
            <m:nary>
              <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/></m:naryPr>
              <m:sub><m:r><m:t>m=1</m:t></m:r></m:sub>
              <m:sup><m:r><m:t>M</m:t></m:r></m:sup>
              <m:e>
                <m:sSup>
                  <m:e>
                    <m:d>
                      <m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr>
                      <m:e>
                        <m:sSub><m:e><m:r><m:t>F</m:t></m:r></m:e><m:sub><m:r><m:t>0</m:t></m:r></m:sub></m:sSub>
                        <m:d><m:dPr><m:begChr m:val="["/><m:endChr m:val="]"/></m:dPr><m:e><m:r><m:t>m</m:t></m:r></m:e></m:d>
                        <m:r><m:t> - </m:t></m:r>
                        <m:bar>
                          <m:barPr><m:pos m:val="top"/></m:barPr>
                          <m:e><m:sSub><m:e><m:r><m:t>F</m:t></m:r></m:e><m:sub><m:r><m:t>0</m:t></m:r></m:sub></m:sSub></m:e>
                        </m:bar>
                      </m:e>
                    </m:d>
                  </m:e>
                  <m:sup><m:r><m:t>2</m:t></m:r></m:sup>
                </m:sSup>
              </m:e>
            </m:nary>
          </m:e>
        </m:rad>
      </m:oMath>
    </m:oMathPara>
    '''
    add_omml_equation_block(doc, omml_eq5, "5")

    # --- Section 5: Experimental Setup ---
    add_sec_heading("5. Experimental Setup & Evaluation Metrics")
    add_body_p(
        "All experiments were conducted using PyTorch 2.x with Metal Performance Shaders (MPS) hardware acceleration on Apple Silicon. "
        "The training framework employs the AdamW optimizer with a LambdaLR schedule consisting of linear warm-up (warmup_ratio = 0.1) "
        "followed by linear learning rate decay to zero. For the Universal HuBERT probe, the model was initialized from the best CREMA-D-trained HuBERT "
        "checkpoint (outputs/cremad/hubert/checkpoints/best_model/model.pt, logged as HuBERT (Transfer from CREMAD)), with the backbone parameters strictly "
        "frozen (encoder_learning_rate = 0.0), and the linear classification head and layer pooling weights adapted on the combined 4-corpus dataset "
        "at a classifier learning rate of 3e-4 with gradient accumulation of 4 steps (effective batch size 64) for 10 epochs (early stopping patience = 4). "
        "The CNN-BiLSTM was optimized at a learning rate of 1e-3 with batch size 32 for 25 epochs (early stopping patience = 5). Class-weighted cross-entropy loss was applied "
        "to mitigate dataset class imbalances:"
    )

    # Equation 6: Cross-Entropy Loss
    omml_eq6 = '''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <m:oMath>
        <m:sSub>
          <m:e><m:r><m:t>ℒ</m:t></m:r></m:e>
          <m:sub><m:r><m:t>CE</m:t></m:r></m:sub>
        </m:sSub>
        <m:r><m:t> = - </m:t></m:r>
        <m:nary>
          <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/></m:naryPr>
          <m:sub><m:r><m:t>k=1</m:t></m:r></m:sub>
          <m:sup><m:r><m:t>K</m:t></m:r></m:sup>
          <m:e>
            <m:sSub><m:e><m:r><m:t>w</m:t></m:r></m:e><m:sub><m:r><m:t>k</m:t></m:r></m:sub></m:sSub>
            <m:sSub><m:e><m:r><m:t>y</m:t></m:r></m:e><m:sub><m:r><m:t>k</m:t></m:r></m:sub></m:sSub>
            <m:r><m:t> log </m:t></m:r>
            <m:sSub>
              <m:e>
                <m:acc>
                  <m:accPr><m:chr m:val="^"/></m:accPr>
                  <m:e><m:r><m:t>y</m:t></m:r></m:e>
                </m:acc>
              </m:e>
              <m:sub><m:r><m:t>k</m:t></m:r></m:sub>
            </m:sSub>
          </m:e>
        </m:nary>
        <m:r><m:t>,   where   </m:t></m:r>
        <m:sSub><m:e><m:r><m:t>w</m:t></m:r></m:e><m:sub><m:r><m:t>k</m:t></m:r></m:sub></m:sSub>
        <m:r><m:t> = </m:t></m:r>
        <m:f>
          <m:num><m:sSub><m:e><m:r><m:t>N</m:t></m:r></m:e><m:sub><m:r><m:t>total</m:t></m:r></m:sub></m:sSub></m:num>
          <m:den><m:r><m:t>K · </m:t></m:r><m:sSub><m:e><m:r><m:t>N</m:t></m:r></m:e><m:sub><m:r><m:t>k</m:t></m:r></m:sub></m:sSub></m:den>
        </m:f>
      </m:oMath>
    </m:oMathPara>
    '''
    add_omml_equation_block(doc, omml_eq6, "6")

    add_body_p(
        "Models were evaluated using Overall Accuracy, Macro-Averaged F1-score, and Unweighted Average Recall (UAR) [13]:"
    )

    # Equation 7: Unweighted Average Recall (UAR)
    omml_eq7 = '''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <m:oMath>
        <m:r><m:t>UAR = </m:t></m:r>
        <m:f>
          <m:num><m:r><m:t>1</m:t></m:r></m:num>
          <m:den><m:r><m:t>K</m:t></m:r></m:den>
        </m:f>
        <m:nary>
          <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/></m:naryPr>
          <m:sub><m:r><m:t>k=1</m:t></m:r></m:sub>
          <m:sup><m:r><m:t>K</m:t></m:r></m:sup>
          <m:e>
            <m:f>
              <m:num><m:sSub><m:e><m:r><m:t>TP</m:t></m:r></m:e><m:sub><m:r><m:t>k</m:t></m:r></m:sub></m:sSub></m:num>
              <m:den>
                <m:sSub><m:e><m:r><m:t>TP</m:t></m:r></m:e><m:sub><m:r><m:t>k</m:t></m:r></m:sub></m:sSub>
                <m:r><m:t> + </m:t></m:r>
                <m:sSub><m:e><m:r><m:t>FN</m:t></m:r></m:e><m:sub><m:r><m:t>k</m:t></m:r></m:sub></m:sSub>
              </m:den>
            </m:f>
          </m:e>
        </m:nary>
      </m:oMath>
    </m:oMathPara>
    '''
    add_omml_equation_block(doc, omml_eq7, "7")

    # Table 3: Experimental Configuration (Actual verified hyperparameters)
    p_cap_hyper = doc.add_paragraph()
    p_cap_hyper.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap_hyper.paragraph_format.space_before = Pt(8)
    p_cap_hyper.paragraph_format.space_after = Pt(2)
    p_cap_hyper_run = p_cap_hyper.add_run("Table 3: Verified Experimental & Hyperparameter Reproducibility Specifications")
    p_cap_hyper_run.font.name = "Times New Roman"
    p_cap_hyper_run.font.size = Pt(9.5)
    p_cap_hyper_run.font.bold = True
    p_cap_hyper_run.font.color.rgb = BLACK

    tbl_hyper_data = [
        ["Configuration Parameter", "Universal HuBERT (CREMA-D-Init Frozen Probe)", "CNN-BiLSTM (Hindi Specialist)"],
        ["Initialization Checkpoint", "CREMA-D HuBERT Checkpoint Transfer", "Random Xavier Initialization"],
        ["Base Architecture / Backbone", "HuBERT-Base (facebook/hubert-base-ls960)", "3-Layer 1D CNN + 2-Layer BiLSTM"],
        ["Input Audio Representation", "Raw Audio Waveform (16 kHz, Mono PCM)", "40 MFCCs (32-ms FFT win, 10-ms hop)"],
        ["Backbone Parameter Status", "Frozen (encoder_lr = 0.0, 0 updates)", "Fully Trainable (End-to-End optimization)"],
        ["Trainable Parameters", "4,626 parameters (~0.005% of 94.7M)", "923,717 parameters (~924K, 100% trainable)"],
        ["Target Emotion Classes", "6 Canonical Classes (English Pool)", "5 Discrete Classes (Hindi Corpus)"],
        ["Optimizer & Weight Decay", "AdamW (weight decay = 0.01)", "AdamW (weight decay = 0.01)"],
        ["Learning Rate (Head / Net)", "3e-4 (Linear Probe + Softmax Layer Weights)", "1e-3 (Full Network)"],
        ["Learning Rate Schedule", "LambdaLR (Linear Warm-up 10% + Linear Decay)", "LambdaLR (Linear Warm-up 10% + Linear Decay)"],
        ["Batching Strategy", "Batch Size = 16, Gradient Accum = 4 (Eff. 64)", "Batch Size = 32, Gradient Accum = 1"],
        ["Maximum Training Epochs", "10 Epochs (Early Stopping Patience = 4)", "25 Epochs (Early Stopping Patience = 5)"],
        ["Hardware & Acceleration", "Apple Silicon MPS (Metal Performance Shaders)", "Apple Silicon MPS (Metal Performance Shaders)"],
    ]
    t_hyper = doc.add_table(rows=len(tbl_hyper_data), cols=len(tbl_hyper_data[0]))
    t_hyper.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_booktabs_borders_bw(t_hyper)
    for r_idx, row in enumerate(tbl_hyper_data):
        for c_idx, val in enumerate(row):
            cell = t_hyper.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if c_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_run = p.runs[0]
            p_run.font.name = "Times New Roman"
            p_run.font.size = Pt(8.5)
            p_run.font.color.rgb = BLACK
            if r_idx == 0:
                p_run.font.bold = True
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # --- Section 6: Results ---
    add_sec_heading("6. Benchmark Results & Comparative Analysis")

    add_subsec_heading("6.1 Universal Multi-Corpus Linear Probe Benchmark")
    add_body_p(
        "To evaluate whether a unified representation can generalize across diverse acoustic environments, accents, and recording conditions, a Universal "
        "HuBERT probe was initialized from the best CREMA-D HuBERT checkpoint (outputs/cremad/hubert/checkpoints/best_model/model.pt, logged as HuBERT "
        "(Transfer from CREMAD)) and subsequently adapted on the combined four-corpus training set, comprising 103 unique training speaker IDs across "
        "CREMA-D, RAVDESS, SAVEE, and TESS (TESS uses prompt-disjoint rather than speaker-disjoint evaluation), and evaluated against 1,701 unseen "
        "multi-corpus test utterances (1,060 CREMA-D + 360 TESS + 176 RAVDESS + 105 SAVEE).\n\n"
        "Across the 1,701 pooled test clips, the Universal HuBERT probe achieves 68.31% aggregate accuracy (0.6779 Macro-F1, 68.61% UAR), outperforming the "
        "zero-shot CREMA-D HuBERT baseline (which achieves 60.61% accuracy, 0.6031 Macro-F1, and 60.54% UAR when transferred directly to the multi-corpus test set) "
        "by an absolute margin of +7.70 percentage points. This gain reflects the combined effect of multi-corpus supervised adaptation and learnable layer pooling "
        "over the single-corpus initialization. Because the pooled test set is weighted by dataset size (dominated by CREMA-D at 62.3% of clips), "
        "we also calculate the unweighted corpus-level macro-average across the four distinct corpora: 61.26% Accuracy, 0.5755 Macro-F1, and 57.54% UAR "
        "(CREMA-D: 72.45% acc / 72.03% UAR; TESS: 68.89% acc / 68.89% UAR; RAVDESS: 52.27% acc / 51.14% UAR; SAVEE: 51.43% acc / 38.10% UAR). "
        "Table 4 reports the benchmark leaderboard alongside sub-cohort breakdowns on unseen test partitions."
    )

    # Table 4: Multi-Corpus Leaderboard
    p_cap2 = doc.add_paragraph()
    p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap2.paragraph_format.space_before = Pt(8)
    p_cap2.paragraph_format.space_after = Pt(2)
    p_cap2_run = p_cap2.add_run("Table 4: Universal Multi-Corpus Test Leaderboard (1,701 Multi-Corpus Test Clips)")
    p_cap2_run.font.name = "Times New Roman"
    p_cap2_run.font.size = Pt(9.5)
    p_cap2_run.font.bold = True
    p_cap2_run.font.color.rgb = BLACK

    tbl2_data = [
        ["Model / Evaluation Strategy", "Test Accuracy", "Macro-F1", "Test UAR", "Status / Scope"],
        ["Universal HuBERT (CREMA-D-Init Frozen Probe)", "68.31%", "0.6779", "68.61%", "Pooled Aggregate (4.1x chance)"],
        ["Zero-Shot CREMA-D HuBERT Baseline", "60.61%", "0.6031", "60.54%", "Direct Multi-Corpus Transfer"],
        ["Corpus-Level Unweighted Macro-Average (4 Corpora)", "61.26%", "0.5755", "57.54%", "Balanced Cross-Corpus Average"],
        ["Sub-Cohort: CREMA-D (1,060 clips, 13 actors)", "72.45%", "0.7232", "72.03%", "Unseen Diverse Actors (IDs 1079-1091)"],
        ["Sub-Cohort: TESS (360 clips, 30 words)", "68.89%", "0.6771", "68.89%", "Prompt-Disjoint Vocabulary Words"],
        ["Sub-Cohort: RAVDESS (176 clips, 4 actors)", "52.27%", "0.5018", "51.14%", "Unseen Professional Actors (21-24)"],
        ["Sub-Cohort: SAVEE (105 clips, 1 actor)", "51.43%", "0.3999", "38.10%", "Single-Speaker SAVEE (Actor KL)"],
        ["Random Chance Baseline", "16.67%", "0.1667", "16.67%", "Theoretical 6-Class Floor"],
    ]
    t2 = doc.add_table(rows=len(tbl2_data), cols=len(tbl2_data[0]))
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_booktabs_borders_bw(t2)
    for r_idx, row in enumerate(tbl2_data):
        for c_idx, val in enumerate(row):
            cell = t2.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if c_idx in [0, 4]:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_run = p.runs[0]
            p_run.font.name = "Times New Roman"
            p_run.font.size = Pt(8.5)
            p_run.font.color.rgb = BLACK
            if r_idx == 0:
                p_run.font.bold = True
            elif r_idx in [1, 2]:
                p_run.font.bold = True
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_figure("fig3_benchmark_performance.png", "Figure 2: Benchmark Accuracy and Macro-F1 across English and Hindi Speech Corpora.", width_in=5.8)

    add_subsec_heading("6.2 In-Domain Multi-Corpus Benchmark Summary")
    add_body_p(
        "Individual in-domain evaluations across all five corpora reveal consistent patterns under controlled evaluation protocols:"
    )

    add_bullet_point("• CREMA-D (91 Actors, 13 Unseen Test Actors): ", "Soft-Voting Top-5 Ensemble achieved 75.57% Accuracy, 0.7594 Macro-F1, and 75.61% UAR under actor-disjoint splits. HuBERT with Learnable Layer Pooling reached 71.98% Accuracy (0.7209 F1), outperforming Wav2Vec2 Base (69.25%) and MFCC+CNN-BiLSTM (63.30%). Wav2Vec2-XLS-R-300M (Frozen Baseline) reached only 24.43% Accuracy (near chance level of 16.67%).", justify=True)
    add_bullet_point("• RAVDESS (24 Actors, Actors 21 to 24 Unseen): ", "Transfer Ensemble achieved 73.75% Accuracy, 0.7207 Macro-F1, and 72.27% UAR. Transfer from CREMA-D pre-training to RAVDESS produced 72.92% Accuracy, compared to 32.50% when trained from scratch using HuBERT alone. Wav2Vec2-XLS-R-300M collapsed to 13.33% Accuracy (barely above chance level of 12.50%).", justify=True)
    add_bullet_point("• SAVEE (4 Actors, Actor KL Unseen): ", "Transfer ensemble reached 51.67% Accuracy, 0.3860 Macro-F1, and 40.48% UAR, substantially surpassing the HuBERT scratch baseline of 25.83% (0.0795 F1) which suffered from vocal tract overfitting. Note: In-domain SAVEE evaluation is conducted on a single unseen British actor (Actor KL, 120 clips), introducing higher empirical variance than multi-actor cohorts.", justify=True)
    add_bullet_point("• Controlled prompt-disjoint evaluation (TESS, 2 Actresses, 200 Words, 30 Unseen Target Words): ", "All in-domain SSL foundation models achieved 100.00% Accuracy and 1.0000 Macro-F1 on prompt-independent splits. When evaluated zero-shot with the multi-corpus Universal HuBERT model, TESS performance settles at 68.89%, illustrating that the 100% in-domain score reflects the constrained acoustic complexity of the two-speaker studio recording on repeated carrier phrases rather than unbounded real-world generalization.", justify=True)

    # Table 5: In-Domain Benchmark Leaderboard
    p_cap3 = doc.add_paragraph()
    p_cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap3.paragraph_format.space_before = Pt(8)
    p_cap3.paragraph_format.space_after = Pt(2)
    p_cap3_run = p_cap3.add_run("Table 5: In-Domain Benchmark Leaderboard Across Evaluated Speech Corpora")
    p_cap3_run.font.name = "Times New Roman"
    p_cap3_run.font.size = Pt(9.5)
    p_cap3_run.font.bold = True
    p_cap3_run.font.color.rgb = BLACK

    tbl3_data = [
        ["Dataset", "Best Model", "Accuracy", "Macro-F1", "UAR", "Chance Floor"],
        ["CREMA-D", "Top-5 Soft-Voting Ensemble", "75.57%", "0.7594", "75.61%", "16.67%"],
        ["RAVDESS", "Transfer Ensemble (CREMA-D)", "73.75%", "0.7207", "72.27%", "12.50%"],
        ["SAVEE (Single Speaker)", "Transfer Ensemble (CREMA-D)", "51.67%", "0.3860", "40.48%", "14.29%"],
        ["TESS (Controlled Prompt)", "TESS-only HuBERT / W2V2", "100.00%", "1.0000", "100.00%", "14.29%"],
        ["Hindi SER (5 Classes)", "CNN-BiLSTM Specialist", "74.42%", "0.7201", "70.85%", "20.00%"],
        ["Hindi SER (5 Classes)", "Top-2 Ensemble (CNN-BiLSTM + LSTM)", "75.19%", "0.7136", "70.56%", "20.00%"],
        ["Combined (Multi-Corpus)", "Universal HuBERT (CREMA-D-Init Probe)", "68.31%", "0.6779", "68.61%", "16.67%"],
    ]
    t3 = doc.add_table(rows=len(tbl3_data), cols=len(tbl3_data[0]))
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_booktabs_borders_bw(t3)
    for r_idx, row in enumerate(tbl3_data):
        for c_idx, val in enumerate(row):
            cell = t3.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if c_idx in [0, 1]:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_run = p.runs[0]
            p_run.font.name = "Times New Roman"
            p_run.font.size = Pt(8.5)
            p_run.font.color.rgb = BLACK
            if r_idx == 0:
                p_run.font.bold = True
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)

    p_t3_note = doc.add_paragraph()
    p_t3_note.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_t3_note.paragraph_format.space_before = Pt(2)
    p_t3_note.paragraph_format.space_after = Pt(6)
    run_t3_note = p_t3_note.add_run(
        "*Note: In experimental benchmarking configs, emotion2vec+ was benchmarked via the facebook/wav2vec2-base proxy architecture "
        "and BEATs via microsoft/wavlm-base-plus under the unified 768-dimensional transformer feature extraction interface. "
        "All transformer backbones are Base variants (12 layers, 768 hidden dimensions). On SAVEE, the single-speaker test set (Actor KL) exhibits "
        "higher variance than multi-speaker test cohorts."
    )
    run_t3_note.font.name = "Times New Roman"
    run_t3_note.font.size = Pt(8.0)
    run_t3_note.font.italic = True
    run_t3_note.font.color.rgb = BLACK

    add_subsec_heading("6.3 Technical Analysis of Wav2Vec2-XLS-R-300M Representation Mismatch")
    add_body_p(
        "Across all evaluated corpora, Wav2Vec2-XLS-R-300M [10] performed near random chance (13.33% on RAVDESS, 24.43% on CREMA-D, 12.50% on SAVEE, "
        "and 19.76% on TESS), underperforming shallow MFCC baselines. Three primary technical factors explain this behavior:"
    )

    add_bullet_point("1. ASR Invariant Pre-training Objective: ", "One possible explanation is that the ASR-oriented pretraining objective encourages phonetic invariance that may reduce the linear separability of affect-related acoustic variation in the frozen final-layer representation.", justify=True)
    add_bullet_point("2. Top-Layer Specialization: ", "Unlike our HuBERT framework which incorporates learnable layer pooling across intermediate depths, the frozen XLS-R baseline extracted features exclusively from its 24th (final) layer. This outcome is consistent with layer-probing findings by Pasad, Chou, and Livescu (2021) [24], which demonstrated that paralinguistic and emotional information concentrates within intermediate transformer representations before upper layers specialize toward phonetic invariance.", justify=True)
    add_bullet_point("3. Capacity-to-Sample Mismatch: ", "Projecting a frozen 1024-dimensional representation from a 317M-parameter model onto tiny target datasets (e.g., 384 SAVEE clips or 960 RAVDESS clips) without layer-wise adaptation creates an acute representation mismatch that prevents effective linear separation.", justify=True)

    # --- Section 7: Ablation Studies ---
    add_sec_heading("7. Empirical Findings & Ablation Studies")

    add_subsec_heading("7.1 Effect of Training Speaker Diversity on Cross-Speaker Generalization")
    add_body_p(
        "Comparing performance across SAVEE (3 training actors), RAVDESS (20 training actors), and CREMA-D (78 training actors) demonstrates a consistent "
        "relationship between speaker cohort size and generalization capability on strictly unseen test speakers. Evaluating HuBERT models trained from "
        "scratch across these datasets reveals that on SAVEE (3 training speakers), HuBERT achieved only 25.83% test accuracy (Macro-F1 0.0795) due to vocal tract "
        "overfitting on the limited speaker cohort. Expanding the training cohort to 20 actors in RAVDESS elevated scratch HuBERT accuracy to 32.50% (and 68.75% for the "
        "scratch ensemble). In CREMA-D, with 78 training actors, HuBERT from scratch reached 71.98% accuracy (and 75.57% for the ensemble). These empirical results "
        "indicate that broader speaker diversity during training is associated with improved speaker-independent generalization across unseen cohorts, "
        "whereas training on minimal speaker cohorts risks acute speaker identity memorization. Because corpus identity, recording conditions, lexical content, "
        "and training-set size vary simultaneously with speaker count, the comparison should not be interpreted as a causal estimate of speaker diversity."
    )

    add_figure("fig2_layer_weights.png", "Figure 3: Empirical Layer Weight Distribution in Learnable Weighted Layer Pooling. Layers 9–11 receive approximately 31.95% of the unrounded normalized weight; exported four-decimal values sum to 99.99% due to rounding.", width_in=5.8)

    add_subsec_heading("7.2 Layer Weight Distribution Across Transformer Depth")
    add_body_p(
        "Figure 3 illustrates the learned softmax weights alpha across the 12 transformer encoder blocks of the Universal HuBERT model, "
        "extracted directly from the trained checkpoint (exported to layer_weights.csv in the repository):"
    )

    add_bullet_point("• Early Layers (Layers 1 to 4): ", "Weights remain basal (alpha_1 = 0.0707, alpha_2 = 0.0710, alpha_3 = 0.0711, alpha_4 = 0.0712, representing 7.07% to 7.12%), capturing low-level spectro-temporal acoustics.", justify=True)
    add_bullet_point("• Intermediate Transition (Layers 5 to 8): ", "Weights steadily increase (alpha_5 = 0.0713, alpha_6 = 0.0717, alpha_7 = 0.0725, alpha_8 = 0.0757, representing 7.13% to 7.57%), reflecting progressive harmonic abstraction.", justify=True)
    add_bullet_point("• Intermediate Prosodic Zone (Layers 9 to 11): ", "Weights reach their empirical maximum (alpha_9 = 0.1001, alpha_10 = 0.1107, alpha_11 = 0.1086), receiving approximately 31.95% of the total normalized layer weight (31.94% when summing the exported four-decimal rounded values: 10.01% + 11.07% + 10.86%). The optimizer assigned its highest weight to Layer 10 (alpha_10 = 0.1107, 11.07%), indicating that the trained downstream probe assigned greater weight to Layers 9–11 under the evaluated protocol, consistent with prior literature [2, 24] noting affective information concentration in intermediate transformer representations.", justify=True)
    add_bullet_point("• Final Layer (Layer 12): ", "Weight decreases slightly to alpha_12 = 0.1053 (10.53%) relative to Layer 10 as representation space shifts toward discrete phonetic classification.", justify=True)
    add_bullet_point("• Normalization Verification: ", "The unrounded softmax weights sum to 1.0000; displayed values are rounded to four decimal places (summing to 99.99% across all 12 layers due to rounding: 7.07% + 7.10% + 7.11% + 7.12% + 7.13% + 7.17% + 7.25% + 7.57% + 10.01% + 11.07% + 10.86% + 10.53%). Table 6 details the layer weights.", justify=True)

    # Table 6: Layer Weights
    p_cap4 = doc.add_paragraph()
    p_cap4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap4.paragraph_format.space_before = Pt(8)
    p_cap4.paragraph_format.space_after = Pt(2)
    p_cap4_run = p_cap4.add_run("Table 6: Layer-Wise Softmax Attention Weight Distribution (HuBERT-Base)")
    p_cap4_run.font.name = "Times New Roman"
    p_cap4_run.font.size = Pt(9.5)
    p_cap4_run.font.bold = True
    p_cap4_run.font.color.rgb = BLACK

    tbl4_data = [
        ["Layer Index", "Softmax Weight", "Percentage", "Interpretive Context (Literature-Informed)"],
        ["Layer 1", "0.0707", "7.07%", "Waveform envelope & low-level spectral energy"],
        ["Layer 2", "0.0710", "7.10%", "Formant structures and spectral slope"],
        ["Layer 3", "0.0711", "7.11%", "Pitch frequency baseline estimation"],
        ["Layer 4", "0.0712", "7.12%", "Spectral flux and voice onset timing"],
        ["Layer 5", "0.0713", "7.13%", "Phonetic-prosodic transition boundary"],
        ["Layer 6", "0.0717", "7.17%", "Intermediate harmonic structure encoding"],
        ["Layer 7", "0.0725", "7.25%", "Broad phonetic category separation"],
        ["Layer 8", "0.0757", "7.57%", "Prosodic phrasing & cadence abstraction"],
        ["Layer 9", "0.1001", "10.01%", "Emotional inflection & macro-prosodic features"],
        ["Layer 10", "0.1107", "11.07%", "Associated with highest learned pooling weight (11.07%)"],
        ["Layer 11", "0.1086", "10.86%", "Global utterance affect & speaker dynamics"],
        ["Layer 12", "0.1053", "10.53%", "Phonetic discrimination & lexical alignment"],
        ["Total Sum", "1.0000", "99.99%*", "The unrounded softmax weights sum to 1.0000 (*99.99% due to 4-decimal rounding)"],
    ]
    t4 = doc.add_table(rows=len(tbl4_data), cols=len(tbl4_data[0]))
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_booktabs_borders_bw(t4)
    for r_idx, row in enumerate(tbl4_data):
        for c_idx, val in enumerate(row):
            cell = t4.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if c_idx in [0, 3]:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_run = p.runs[0]
            p_run.font.name = "Times New Roman"
            p_run.font.size = Pt(8.5)
            p_run.font.color.rgb = BLACK
            if r_idx == 0:
                p_run.font.bold = True
            elif r_idx in [9, 10, 11]:
                p_run.font.bold = True
            elif r_idx == len(tbl4_data) - 1:
                p_run.font.bold = True
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_subsec_heading("7.3 Cross-Lingual Adaptation to Indic Hindi Speech")
    add_body_p(
        "To evaluate cross-lingual transferability, the English-trained Universal HuBERT model was evaluated zero-shot on the unseen Hindi test split. "
        "Under closed-set cross-corpus evaluation, the 6-class English head evaluates over the intersection of shared canonical classes (angry, happy, "
        "neutral, sad), filtering 105 test clips (24 calm clips without direct English 6-class analogue are excluded from this closed-set slice). "
        "Universal HuBERT achieves 27.62% accuracy and 31.76% UAR without any target fine-tuning, exceeding the 25.00% 4-class random chance baseline.\n\n"
        "In contrast, supervised adaptation using the specialized CNN-BiLSTM architecture trained directly on the 5-class Hindi training partition "
        "achieves 74.42% test accuracy, 0.7201 Macro-F1, and 70.85% UAR across all 129 test clips (with the Top-2 ensemble reaching 75.19% accuracy and "
        "70.56% UAR against a 20.00% 5-class chance floor). This represents an absolute gain of 46.80 percentage points (47.57 points for the ensemble) "
        "over zero-shot transfer, demonstrating the substantial value of in-domain supervised adaptation for the evaluated Hindi task. "
        "Figure 4 illustrates this comparison, and Figure 5 displays the corresponding normalized confusion matrix generated directly from test predictions."
    )

    add_figure("fig4_cross_lingual_transfer.png", "Figure 4: Cross-Lingual Adaptation to Indic Hindi Speech (Zero-Shot vs. Supervised Adaptation).", width_in=5.8)
    add_figure("fig5_hindi_confusion_matrix.png", "Figure 5: Normalized Confusion Matrix for the Hindi Emotion Specialist Model (74.42% Test Accuracy).", width_in=4.8)

    # --- Section 8: Behavioural Telemetry ---
    add_sec_heading("8. Speech Behavioural Intelligence Profiling")
    add_body_p(
        "Continuous acoustic telemetry provides objective measurements of speech behaviour that systematically characterize categorical emotional states "
        "without asserting clinical psychological diagnosis. Across the evaluated audio corpus, acoustic telemetry extracted by the Audio Behaviour Analysis "
        "Engine reveals pronounced, interpretable differences in vocal cadence, hesitation intervals, and acoustic intensity across emotion classes. "
        "Table 7 summarizes these empirical telemetry profiles across the five evaluated emotion categories, and Figure 6 illustrates the corresponding multi-dimensional acoustic patterns:"
    )

    # Table 7: Behavioural Telemetry Profiles (Aligned directly with Figure 6)
    p_cap_beh = doc.add_paragraph()
    p_cap_beh.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap_beh.paragraph_format.space_before = Pt(8)
    p_cap_beh.paragraph_format.space_after = Pt(2)
    p_cap_beh_run = p_cap_beh.add_run("Table 7: Acoustic Behavioural Telemetry Profiles Across Discrete Emotion Categories")
    p_cap_beh_run.font.name = "Times New Roman"
    p_cap_beh_run.font.size = Pt(9.5)
    p_cap_beh_run.font.bold = True
    p_cap_beh_run.font.color.rgb = BLACK

    tbl_beh_data = [
        ["Emotion Category", "N", "Speaking Speed (syl/s)", "Pause Ratio (%)", "RMS Energy (dB)", "Mean Pitch F0 (Hz)", "Observed Acoustic Behaviour Profile"],
        ["Angry", "15", "2.82 ± 0.21", "26.5 ± 10.0%", "-27.8 ± 3.2 dB", "224.7 ± 98.7 Hz", "Elevated pitch frequency (224.7 Hz), wide pitch variation (std: 56.4 Hz), reduced hesitation"],
        ["Calm", "24", "3.15 ± 0.55", "34.4 ± 13.1%", "-27.1 ± 3.1 dB", "162.8 ± 44.5 Hz", "Highest pause ratio (34.4%), measured vocal cadence, lower pitch baseline (162.8 Hz)"],
        ["Happy", "12", "2.72 ± 0.17", "24.5 ± 7.5%", "-23.7 ± 3.6 dB", "200.8 ± 81.7 Hz", "Highest vocal loudness (-23.7 dB RMS), lowest pause ratio (24.5%), high pitch (200.8 Hz)"],
        ["Neutral", "55", "2.90 ± 0.29", "34.0 ± 10.5%", "-27.4 ± 3.0 dB", "165.7 ± 73.0 Hz", "Baseline conversational cadence (2.90 syl/s), moderate energy (-27.4 dB), stable pitch"],
        ["Sad", "23", "2.89 ± 0.44", "28.6 ± 11.0%", "-29.6 ± 6.7 dB", "165.6 ± 54.1 Hz", "Lowest acoustic energy (-29.6 dB RMS), attenuated vocal dynamics, moderate pauses"],
    ]
    t_beh = doc.add_table(rows=len(tbl_beh_data), cols=len(tbl_beh_data[0]))
    t_beh.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_booktabs_borders_bw(t_beh)
    for r_idx, row in enumerate(tbl_beh_data):
        for c_idx, val in enumerate(row):
            cell = t_beh.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if c_idx in [0, 5]:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_run = p.runs[0]
            p_run.font.name = "Times New Roman"
            p_run.font.size = Pt(8.5)
            p_run.font.color.rgb = BLACK
            if r_idx == 0:
                p_run.font.bold = True
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)

    p_tbeh_note = doc.add_paragraph()
    p_tbeh_note.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_tbeh_note.paragraph_format.space_before = Pt(2)
    p_tbeh_note.paragraph_format.space_after = Pt(6)
    run_tbeh_note = p_tbeh_note.add_run("*Note: Empirical acoustic telemetry extracted directly from all 129 evaluation audio clips by scripts/extract_behavior_profiles.py (archived in outputs/behavior/emotion_profiles.csv). Values represent Mean ± Standard Deviation.")
    run_tbeh_note.font.name = "Times New Roman"
    run_tbeh_note.font.size = Pt(8.0)
    run_tbeh_note.font.italic = True
    run_tbeh_note.font.color.rgb = BLACK

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_figure("fig6_behavioral_prosody_profile.png", "Figure 6: Multimodal Speech Behaviour Telemetry (Mean ± 1 SD) across Discrete Emotion Categories (Empirical Measurements).", width_in=6.0)

    # --- Section 9: Deployment Architecture ---
    add_sec_heading("9. System Deployment Architecture & Hardware Latency Benchmark")
    add_body_p(
        "The complete framework is implemented as an Apple Silicon accelerated microservice paired with a minimal web application. "
        "Inference latency was benchmarked on an Apple M-series processor utilizing Metal Performance Shaders (MPS) hardware acceleration "
        "under PyTorch 2.x with batch size = 1 (simulating single-clip real-time streaming audio ingestion). Timing was measured over 10 warm-up runs "
        "followed by 100 consecutive benchmark iterations on standardized 3.0-second audio clips:"
    )

    add_bullet_point("• Backend Microservice (FastAPI): ", "Model registry serving the Hindi Specialist (CNN-BiLSTM) and Universal SER models. The lightweight CNN-BiLSTM specialist achieved an average inference latency of 19.94 ms per clip (std: 1.2 ms), while the 12-layer Universal HuBERT model achieved 191.44 ms per clip (std: 5.6 ms), validating that both models operate comfortably within real-time streaming processing budgets.", justify=True)
    add_bullet_point("• Frontend UI (Next.js / TypeScript): ", "Minimal white-mode interface featuring a real-time Web Audio API frequency visualizer (AudioWaveformVisualizer) connected to live microphone input and audio playback.", justify=True)

    # --- Section 10: Discussion ---
    add_sec_heading("10. Discussion & Limitations")
    add_body_p(
        "While the experimental results validate the efficacy of learnable layer pooling and disjoint evaluation protocols, several limitations should be noted:"
    )

    add_bullet_point("1. Constrained Recording Environments: ", "Corpora such as TESS feature near-zero ambient noise and fixed carrier phrases, yielding ceiling-level performance (100.00%) that does not represent conversational, noisy real-world speech.", justify=True)
    add_bullet_point("2. Single-Speaker Evaluation Cohort: ", "In-domain SAVEE evaluation isolates a single test speaker (Actor KL, 105 to 120 clips), resulting in higher statistical variance than diverse multi-speaker cohorts such as CREMA-D.", justify=True)
    add_bullet_point("3. Indic Dialectal Diversity: ", "The Hindi evaluation was conducted across 14 unique speakers; regional dialectal variations across northern and central India require broader multi-dialect data collection.", justify=True)
    add_bullet_point("4. Pre-trained Audio Bandwidth: ", "Standard foundation models operate at 16 kHz sampling rates, which truncates ultra-high frequency acoustic cues (> 8 kHz).", justify=True)

    # --- Section 11: Conclusion ---
    add_sec_heading("11. Conclusion")
    add_body_p(
        "This research evaluated speech emotion recognition across multi-corpus and cross-lingual settings. The primary conclusions are:"
    )

    add_bullet_point("1. Learnable Weighted Layer Pooling: ", "The learned pooling mechanism assigned its highest aggregate weight to Layers 9–11, which together received approximately 31.95% of the normalized layer weight. This indicates that the downstream probe preferentially weighted these intermediate representations under the evaluated multi-corpus protocol.", justify=True)
    add_bullet_point("2. Effect of Training Speaker Diversity: ", "Broad multi-speaker training cohorts are associated with improved generalization: models trained on minimal speaker cohorts overfit individual speaker vocal tract geometry, whereas diverse cohorts support robust speaker-independent evaluation.", justify=True)
    add_bullet_point("3. Cross-Lingual Transfer & Supervised Adaptation: ", "English pre-trained models transfer moderately above chance (27.62% vs. 25.00% floor) to Hindi speech, but supervised adaptation using specialized CNN-BiLSTM networks achieves 74.42% accuracy (75.19% via ensemble fusion), representing a +46.80% single-model performance gain.", justify=True)
    add_bullet_point("4. Continuous Behavioural Telemetry: ", "Combining discrete emotion classification with continuous acoustic measurements (speaking rate, pause ratio, RMS energy, and pitch variability) provides interpretable vocal characterization to complement categorical predictions.", justify=True)

    # --- Section: References ---
    add_sec_heading("References")

    references = [
        '[1] S. Kotian and S. Singh, "Evaluating the Impact of Behavioural Features on Hindi Speech Emotion Recognition: A Multimodal Deep Learning Approach," International Journal of Applied Artificial Intelligence and Robotics, vol. 2, no. 1, art. 9, pp. 1–15, Mar. 2026, doi: 10.67745/ijaic.v2i1.9. [Online]. Available: https://doi.org/10.67745/ijaic.v2i1.9.',
        '[2] S.-w. Yang, P.-H. Chi, Y.-S. Chuang, C.-I. J. Lai, K. Lakhotia, Y. Y. Lin, A. T. Liu, J. Shi, X. Chang, G.-T. Lin et al., "SUPERB: Speech Processing Universal PERformance Benchmark," in Proc. Interspeech 2021, Brno, Czech Republic, 2021, pp. 1194–1198, doi: 10.21437/Interspeech.2021-1775.',
        '[3] K. Chauhan, K. K. Sharma, and T. Varma, "MNITJ-SEHSD: A Hindi Emotional Speech Database," in Proc. 2023 International Conference on Communication, Circuits, and Systems (IC3S), Bhubaneswar, India, 2023, pp. 1–6, doi: 10.1109/IC3S57698.2023.10169497.',
        '[4] P. Mehra and S. K. Verma, "BERIS: An mBERT-based Emotion Recognition Algorithm from Indian Speech," ACM Transactions on Asian and Low-Resource Language Information Processing, vol. 21, no. 5, art. 106, pp. 1–19, Apr. 2022, doi: 10.1145/3517195.',
        '[5] R. Kawade and S. Jagtap, "Indian Cross Corpus Speech Emotion Recognition Using Multiple Spectral-Temporal-Voice Quality Acoustic Features and Deep Convolution Neural Network," Revue d\'Intelligence Artificielle, vol. 38, no. 3, pp. 913–927, Jun. 2024, doi: 10.18280/ria.380318.',
        '[6] Z. Ma, Z. Zheng, J. Ye, J. Li, Z. Gao, S. Zhang, and X. Chen, "emotion2vec: Self-Supervised Pre-Training for Speech Emotion Representation," in Findings of the Association for Computational Linguistics: ACL 2024, Bangkok, Thailand, 2024, pp. 15747–15760, doi: 10.18653/v1/2024.findings-acl.931.',
        '[7] S. Chen, Y. Wu, C. Wang, S. Liu, D. Tompkins, Z. Chen, and F. Wei, "BEATs: Audio Pre-Training with Acoustic Tokenizers," in Proc. 40th International Conference on Machine Learning (ICML), vol. 202, 2023, pp. 5178–5193.',
        '[8] W.-N. Hsu, B. Bolte, Y.-H. H. Tsai, K. Lakhotia, R. Salakhutdinov, and A. Mohamed, "HuBERT: Self-Supervised Speech Representation Learning by Masked Prediction of Hidden Units," IEEE/ACM Transactions on Audio, Speech, and Language Processing, vol. 29, pp. 3451–3460, 2021, doi: 10.1109/TASLP.2021.3122291.',
        '[9] A. Baevski, Y. Zhou, A. Mohamed, and M. Auli, "wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations," in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, 2020, pp. 12449–12460.',
        '[10] A. Babu, C. Wang, A. Tjandra, K. Lakhotia, Q. Xu, N. Goyal, K. Singh, P. von Platen, Y. Saraf, J. Pino, A. Baevski, A. Conneau, and M. Auli, "XLS-R: Self-supervised Cross-lingual Speech Representation Learning at Scale," in Proc. Interspeech 2022, Incheon, Korea, 2022, pp. 2278–2282, doi: 10.21437/Interspeech.2022-143.',
        '[11] J. H. Chowdhury, S. Ramanna, and K. Kotecha, "Speech emotion recognition with light weight deep neural ensemble model using hand crafted features," Scientific Reports, vol. 15, no. 1, art. 11824, pp. 1–14, 2025, doi: 10.1038/s41598-025-95734-z. [Online]. Available: https://www.nature.com/articles/s41598-025-95734-z.',
        '[12] F. Eyben, K. R. Scherer, B. W. Schuller, J. Sundberg, E. André, C. Busso, L. Y. Devillers, J. Epps, P. Laukka, S. S. Narayanan, and K. P. Truong, "The Geneva Minimalistic Acoustic Parameter Set (GeMAPS) for Voice Research and Affective Computing," IEEE Transactions on Affective Computing, vol. 7, no. 2, pp. 190–202, Apr.–Jun. 2016, doi: 10.1109/TAFFC.2015.2457417.',
        '[13] B. W. Schuller, A. Batliner, C. Bergler, E.-M. Messner, A. Hamilton, S. Amiriparian, A. Baird, G. Rizos, M. Schmitt, L. Stappen, H. Baumeister, A. D. MacIntyre, and S. Hantke, "The INTERSPEECH 2020 Computational Paralinguistics Challenge: Elderly Emotion, Breathing & Masks," in Proc. Interspeech 2020, Shanghai, China, 2020, pp. 2042–2046, doi: 10.21437/Interspeech.2020-32.',
        '[14] N. Wang and D. Yang, "Speech emotion recognition using fine-tuned Wav2vec2.0 and neural controlled differential equations classifier," PLoS ONE, vol. 20, no. 2, art. e0318297, pp. 1–13, Feb. 2025, doi: 10.1371/journal.pone.0318297.',
        '[15] A. Hashem, M. Arif, and M. Alghamdi, "Speech emotion recognition approaches: A systematic review," Speech Communication, vol. 154, art. 102974, pp. 1–29, Oct. 2023, doi: 10.1016/j.specom.2023.102974.',
        '[16] M. B. Akçay and K. Oğuz, "Speech emotion recognition: Emotional models, databases, features, preprocessing methods, supporting modalities, and classifiers," Speech Communication, vol. 116, pp. 56–76, Jan. 2020, doi: 10.1016/j.specom.2019.12.001.',
        '[17] H. Cao, D. G. Cooper, M. K. Keutmann, R. C. Gur, A. Nenkova, and R. Verma, "CREMA-D: Crowd-Sourced Emotional Multimodal Actors Dataset," IEEE Transactions on Affective Computing, vol. 5, no. 4, pp. 377–390, Oct.–Dec. 2014, doi: 10.1109/TAFFC.2014.2336244.',
        '[18] S. R. Livingstone and F. A. Russo, "The Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS): A dynamic, multimodal set of facial and vocal expressions in North American English," PLoS ONE, vol. 13, no. 5, art. e0196391, pp. 1–33, May 2018, doi: 10.1371/journal.pone.0196391.',
        '[19] S. Haq and P. J. B. Jackson, "Multimodal Emotion Recognition," in Machine Audition: Principles, Algorithms and Systems, W. Wang, Ed., Hershey, PA: IGI Global, 2010, pp. 398–423, doi: 10.4018/978-1-61520-919-4.ch017.',
        '[20] M. K. Pichora-Fuller and K. Dupuis, "Toronto Emotional Speech Set (TESS)," Scholars Portal Dataverse, vol. 1, 2020, doi: 10.5683/SP2/E8H2MF.',
        '[21] A. Goel, M. Hira, and A. Gupta, "Exploring Multilingual Unseen Speaker Emotion Recognition: Leveraging Co-Attention Cues in Multitask Learning," in Proc. Interspeech 2024, Kos Island, Greece, 2024, pp. 2340–2344, doi: 10.21437/Interspeech.2024-1820.',
        '[22] H. Rathnayake, J. James, G. Leoni, A. Nicholas, C. Watson, and P. Keegan, "A review on speech emotion recognition for low-resource and Indigenous languages," Speech Communication, vol. 176, art. 103342, pp. 1–25, Jan. 2026, doi: 10.1016/j.specom.2025.103342.',
        '[23] S. T. Alam Monisha and S. Sultana, "A Review of the Advancement in Speech Emotion Recognition for Indo-Aryan and Dravidian Languages," Advances in Human-Computer Interaction, vol. 2022, art. 9602429, pp. 1–11, Dec. 2022, doi: 10.1155/2022/9602429.',
        '[24] A. Pasad, J.-C. Chou, and K. Livescu, "Layer-wise Analysis of a Self-supervised Speech Representation Model," in Proc. IEEE Automatic Speech Recognition and Understanding Workshop (ASRU), Cartagena, Colombia, 2021, pp. 914–921, doi: 10.1109/ASRU51503.2021.9688093.',
        '[25] J. Wagner, D. Schiller, A. Seiderer, and E. André, "Deep learning in paralinguistic recognition tasks: Are hand-crafted features still relevant?," in Proc. Interspeech 2018, Hyderabad, India, 2018, pp. 147–151, doi: 10.21437/Interspeech.2018-1238.',
        '[26] S. Latif, R. Rana, S. Khalifa, R. Jurdak, J. Qadir, and B. W. Schuller, "Survey of Deep Representation Learning for Speech Emotion Recognition," IEEE Transactions on Affective Computing, vol. 14, no. 2, pp. 1634–1654, Apr.–Jun. 2023, doi: 10.1109/TAFFC.2021.3114365.',
        '[27] L. Pepino, P. Riera, and L. Ferrer, "Emotion Recognition from Speech Using wav2vec 2.0 Embeddings," in Proc. Interspeech 2021, Brno, Czech Republic, 2021, pp. 3400–3404, doi: 10.21437/Interspeech.2021-703.',
        '[28] C. Busso, M. Bulut, C.-C. Lee, A. Kazemzadeh, E. Mower, S. Kim, J. N. Chang, S. Lee, and S. S. Narayanan, "IEMOCAP: Interactive emotional dyadic motion capture database," Language Resources and Evaluation, vol. 42, no. 4, pp. 335–359, Dec. 2008, doi: 10.1007/s10579-008-9076-6.',
        '[29] M. Mauch and S. Dixon, "pYIN: A Fundamental Frequency Estimator Using Probabilistic Threshold Distributions," in Proc. IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP), Florence, Italy, 2014, pp. 659–663, doi: 10.1109/ICASSP.2014.6853678.',
        '[30] C. Sun, Y. Zhou, X. Huang, J. Yang, and X. Hou, "Combining wav2vec 2.0 Fine-Tuning and ConLearnNet for Speech Emotion Recognition," Electronics, vol. 13, no. 6, art. 1103, pp. 1–19, Mar. 2024, doi: 10.3390/electronics13061103.',
        '[31] Sarthwa8, "Indian TTS Emotion 60min: Speech Emotion Dataset for Indian English and Hindi," Hugging Face Datasets, 2023. [Online]. Available: https://huggingface.co/datasets/sarthwa8/indian-tts-emotion-60min.',
        '[32] Ghostieee11, "Vaani Speech Corpus: Multilingual Indic Speech Dataset," Hugging Face Datasets, 2023. [Online]. Available: https://huggingface.co/datasets/ghostieee11/vaani-speech-corpus.',
        '[33] RapidOrc121, "Audio Emotion Detection Dataset," Hugging Face Datasets, 2023. [Online]. Available: https://huggingface.co/datasets/RapidOrc121/audio-emotion-detection-dataset.'
    ]

    for ref in references:
        rp = doc.add_paragraph()
        rp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        rp.paragraph_format.left_indent = Inches(0.25)
        rp.paragraph_format.first_line_indent = Inches(-0.25)
        rp.paragraph_format.line_spacing = 1.1
        rp.paragraph_format.space_before = Pt(0)
        rp.paragraph_format.space_after = Pt(2.5)
        run_ref = rp.add_run(ref)
        run_ref.font.name = "Times New Roman"
        run_ref.font.size = Pt(8.5)
        run_ref.font.color.rgb = BLACK

    doc.save(str(DOCX_OUT))
    doc.save(str(DESKTOP_DOCX))
    print(f"Successfully generated clean Word report with optimized alignment: {DOCX_OUT} and {DESKTOP_DOCX}")


if __name__ == "__main__":
    build_clean_word_report()
