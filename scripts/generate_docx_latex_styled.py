"""
Script to generate an impeccably aligned, publication-grade Microsoft Word (.docx) research report.
Applies intelligent content-aware alignment:
- Full narrative body paragraphs and multi-line descriptive points: JUSTIFIED for clean academic margins.
- Short list items, concise points, section headings, and references: LEFT-ALIGNED to eliminate awkward word-stretching.
- Numerical metric columns and table titles: CENTER-ALIGNED for crisp tabular clarity.
- Figure captions and display equations: CENTER-ALIGNED with right-aligned equation numbers.
- Clean and minimal headers/footers: Empty header, simple centered page number in footer (zero lines, zero IEEE clutter).
- 100% Pure Black text (RGB: 0, 0, 0) throughout.

Author: Himanshi Patel
Department of Computer Science and Engineering
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
DESKTOP_DOCX = Path("/Users/prarthanapatel/Desktop/Himanshi/FINAL_RESEARCH_REPORT.docx")
FIG_DIR = Path("reports/figures")

BLACK = RGBColor(0, 0, 0)


def set_cell_margins(cell, top=70, bottom=70, left=90, right=90):
    """Set inner cell padding in twips."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_booktabs_borders_bw(table):
    """
    Applies clean LaTeX booktabs borders:
    Thick top border (1.5pt solid black), medium header bottom border (0.75pt solid black),
    thick bottom border (1.5pt solid black), thin internal row border (0.25pt),
    and zero vertical lines.
    """
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        f'  <w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D1D5DB"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def add_omml_equation_block(doc, omml_xml, eq_num=""):
    """Adds a native Word OMML display equation with right-aligned numbering in pure black."""
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(5.7)
    tbl.columns[1].width = Inches(0.8)

    # Hide all borders on equation table
    tblPr = tbl._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="none"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:insideH w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

    cell_eq = tbl.cell(0, 0)
    p_eq = cell_eq.paragraphs[0]
    p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq.paragraph_format.space_before = Pt(3)
    p_eq.paragraph_format.space_after = Pt(3)
    p_eq._p.append(parse_xml(omml_xml))

    cell_num = tbl.cell(0, 1)
    p_num = cell_num.paragraphs[0]
    p_num.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_num.paragraph_format.space_before = Pt(3)
    p_num.paragraph_format.space_after = Pt(3)
    if eq_num:
        run_num = p_num.add_run(f"({eq_num})")
        run_num.font.name = "Times New Roman"
        run_num.font.size = Pt(10)
        run_num.font.color.rgb = BLACK

    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build_clean_word_report():
    doc = docx.Document()

    # --- Page Setup: Letter with 1.0 inch academic margins ---
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    # Clean header: completely empty, no lines, no IEEE banners
    header = section.header
    p_head = header.paragraphs[0]
    p_head.text = ""

    # Clean footer: simple centered page number, no lines, no IEEE text
    footer = section.footer
    p_foot = footer.paragraphs[0]
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.paragraph_format.space_before = Pt(6)
    p_foot.paragraph_format.space_after = Pt(0)
    
    # Append dynamic page number field in pure black
    fld_page = parse_xml(r'<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:instr="PAGE"/>')
    p_foot._p.append(fld_page)

    # Set Default Document Font
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(10)
    normal_style.font.color.rgb = BLACK

    # --- Document Title (Centered) ---
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(8)
    p_title.paragraph_format.line_spacing = 1.22
    run_title = p_title.add_run(
        "Multi-Corpus and Multilingual Speech Emotion Recognition with Audio Behavioural Intelligence: "
        "A Cross-Lingual Evaluation and Learnable Weighted Layer Pooling Study"
    )
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = BLACK

    # --- Author Block (Centered) ---
    p_author = doc.add_paragraph()
    p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_author.paragraph_format.space_before = Pt(0)
    p_author.paragraph_format.space_after = Pt(3)
    run_author = p_author.add_run("Himanshi Patel")
    run_author.font.name = 'Times New Roman'
    run_author.font.bold = True
    run_author.font.size = Pt(12)
    run_author.font.color.rgb = BLACK

    p_affil = doc.add_paragraph()
    p_affil.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_affil.paragraph_format.space_before = Pt(0)
    p_affil.paragraph_format.space_after = Pt(16)
    run_affil = p_affil.add_run(
        "Department of Computer Science and Engineering\n"
        "Project Repository: speech_emotion_detection (Branch: develop-v3)"
    )
    run_affil.font.name = 'Times New Roman'
    run_affil.font.size = Pt(9.5)
    run_affil.font.italic = True
    run_affil.font.color.rgb = BLACK

    # --- Abstract & Keywords Block (Justified narrative, Left-aligned tag) ---
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
        "Speech Emotion Recognition (SER) is an active area of investigation within human-computer interaction, "
        "psychiatric diagnostics, and automated voice analysis. However, contemporary SER research faces several methodological "
        "constraints. First, randomized dataset partitioning causes speaker identity leakage, which has been shown in recent "
        "paralinguistic literature [21] to artificially inflate experimental accuracy by overestimating generalization to novel speakers. "
        "Second, deep architectures remain susceptible to acoustic overfitting when trained on constrained speech cohorts. Third, the "
        "literature exhibits a pronounced focus on Germanic and Romance languages, offering limited empirical evidence on cross-lingual "
        "transferability to morphologically rich Indic languages such as Hindi. Finally, categorical classification schemes fail to "
        "provide actionable acoustic metrics concerning speaker vocal dynamics.\n\n"
        "To address these limitations, this study presents a standardized empirical evaluation comprising two decoupled experimental protocols "
        "across five speech corpora totaling 12,180 standardized audio recordings: (1) a multi-corpus English benchmark combining four established "
        "corpora (CREMA-D, RAVDESS, SAVEE, and TESS, totaling 11,318 clips across 121 speakers) to evaluate cross-corpus generalization and layer-pooling "
        "dynamics under strict speaker-disjoint splits, and (2) a standalone cross-lingual transfer and native adaptation study on an Indic speech corpus "
        "(862 native Hindi utterances across 25 speakers). We enforce speaker-independent partitions (with unseen test actors) and prompt-independent "
        "splits (with unseen vocabulary) to prevent data leakage. Following the SUPERB benchmark methodology [2], we implement a Learnable "
        "Weighted Layer Pooling mechanism coupled with a linear classification probe across the 12 transformer hidden layers of a frozen "
        "self-supervised foundation backbone (HuBERT-Base, training only 4,626 parameters). Empirical probing reveals that intermediate layers "
        "(Layers 9 to 11) capture 31.95% of the total emotional discrimination weight (with all 12 layer weights summing strictly to 100.00%), "
        "demonstrating that intermediate representations retain strong emotional salience compared to early acoustic representations.\n\n"
        "Additionally, cross-lingual transfer from the English multi-corpus foundation model yields 27.62% accuracy and 31.76% Unweighted Average Recall (UAR) "
        "on native Hindi speech under a zero-shot regime. Supervised adaptation using a specialized CNN-BiLSTM architecture increases test accuracy "
        "to 74.42% (75.19% via ensemble fusion) and UAR to 70.85% (70.56% ensemble). Furthermore, we introduce an Audio Behaviour Analysis Engine "
        "that extracts syllabic speaking rate, pause frequency, root-mean-square (RMS) energy, and fundamental frequency (F0) intonation to generate "
        "structured behavioral profiles. The full system is deployed as an Apple Silicon accelerated microservice paired with a minimal web application "
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

    # --- Typography Helpers with Intelligent Alignment ---
    def add_sec_heading(title):
        """Major section heading: LEFT-ALIGNED, bold, clean spacing."""
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = BLACK

    def add_subsec_heading(title):
        """Subsection heading: LEFT-ALIGNED, bold, clean spacing."""
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = BLACK

    def add_body_p(text, indent=True):
        """Standard narrative paragraph: JUSTIFIED with 0.2 inch first-line indent."""
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3.5)
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.2)
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        run.font.color.rgb = BLACK
        return p

    def add_bullet_point(tag_bold, text_body, justify=True):
        """
        List/bullet item with hanging indent.
        - Multi-line descriptive points: JUSTIFIED.
        - Short points: LEFT-ALIGNED.
        """
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.2)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)

        run_tag = p.add_run(tag_bold)
        run_tag.font.name = "Times New Roman"
        run_tag.font.size = Pt(9.5)
        run_tag.font.bold = True
        run_tag.font.color.rgb = BLACK

        run_body = p.add_run(text_body)
        run_body.font.name = "Times New Roman"
        run_body.font.size = Pt(9.5)
        run_body.font.color.rgb = BLACK
        return p

    def add_short_list_item(num_str, tag_bold, text_body):
        """Concise list item: LEFT-ALIGNED (no justified stretching)."""
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.2)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2.5)

        run_num = p.add_run(f"{num_str}. ")
        run_num.font.name = "Times New Roman"
        run_num.font.size = Pt(9.5)
        run_num.font.bold = True
        run_num.font.color.rgb = BLACK

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
        """Centered image with centered caption."""
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

    add_subsec_heading("1.3 Integrating Objective Vocal Metrics")
    add_body_p(
        "Standard SER architectures typically output discrete emotion class probabilities, such as P(Happy) = 0.85. However, clinical diagnostic "
        "applications, tele-counseling, and automated conversational systems benefit from continuous, interpretable acoustic measurements [5], [11], [12]:"
    )

    # 4 Vocal Metrics: Short concise points -> LEFT-ALIGNED
    add_short_list_item("1", "Speech Velocity (syllables/s)", "Indicates psychomotor tempo and affective activation state.")
    add_short_list_item("2", "Pause Frequency and Duration", "Reflects cognitive hesitation, processing load, and structural fluency.")
    add_short_list_item("3", "Vocal Energy Variation", "Measures behavioral engagement and acoustic intensity dynamics.")
    add_short_list_item("4", "Fundamental Pitch (F0) Variation", "Quantifies dynamic pitch inflection versus flattened vocal affect.")

    add_body_p(
        "Coupling categorical emotion classification with systematic behavioral feature extraction provides a more informative assessment of speech recordings [1], [11], [25]."
    )

    add_subsec_heading("1.4 Research Questions (RQ)")
    add_body_p("This study addresses four primary research questions:")

    # 4 RQs: Multi-line descriptive questions -> JUSTIFIED with bold tag
    add_bullet_point("• RQ1 (Layer Pooling Dynamics): ", "Does learnable weighted pooling across all transformer hidden layers outperform standard mean pooling or top-layer classification, and which layers encode the most discriminative emotional information?", justify=True)
    add_bullet_point("• RQ2 (Speaker Diversity Law): ", "What is the relationship between the number of training speakers and out-of-domain generalization performance on strictly unseen actors?", justify=True)
    add_bullet_point("• RQ3 (Cross-Lingual Transfer to Indic Speech): ", "To what degree do English multi-corpus representations transfer zero-shot to native Hindi speech, and what performance gain is achieved via supervised adaptation?", justify=True)
    add_bullet_point("• RQ4 (Behavioral Telemetry Integration): ", "How effectively do continuous acoustic features (speech tempo, pause ratio, energy, and pitch intonation) correlate with categorical emotion classifications?", justify=True)

    # --- Section 2: Literature Survey ---
    add_sec_heading("2. Related Work & Literature Survey")
    add_body_p(
        "This investigation synthesizes 30 peer-reviewed publications across four core theoretical domains:"
    )

    add_subsec_heading("2.1 Indic and Hindi Speech Emotion Recognition")
    add_body_p(
        "Early speech emotion recognition research in India relied predominantly on small private datasets evaluated with conventional "
        "classifiers such as Support Vector Machines (SVM) and Multi-Layer Perceptrons [4], [16]. Kotian and Singh (2026) [1] demonstrated "
        "that concatenating prosodic-behavioral descriptors (speaking rate, pitch perturbation, pause ratio, and energy dynamics) with spectral "
        "features enhanced classification accuracy and macro-F1 on Hindi speech under challenging acoustic conditions. Chauhan, Sharma, and "
        "Varma (2023) [3] introduced the MNITJ-SEHSD database, standardizing an Indic emotion corpus and highlighting acoustic overlap "
        "between anger and disgust resulting from shared high vocal intensity. Kawade and Jagtap (2024) [5] evaluated cross-lingual acoustic modeling "
        "across Indian speech corpora, demonstrating the effectiveness of combining multiple spectral, temporal, and voice quality descriptors with deep "
        "convolutional neural networks. Rathnayake et al. (2026) [22] and Alam Monisha and Sultana (2022) [23] provided comprehensive surveys on the unique "
        "acoustic-phonetic challenges and database resources in low-resource Indo-Aryan and Dravidian speech emotion recognition."
    )

    add_subsec_heading("2.2 Self-Supervised Speech Representation Models")
    add_body_p(
        "Self-supervised learning has established powerful baseline representations for speech tasks. Models such as Wav2Vec 2.0 (Baevski et al., 2020) [9] "
        "and HuBERT (Hsu et al., 2021) [8] learn representations from thousands of hours of unlabeled audio through contrastive loss or masked cluster prediction. "
        "Yang et al. (2021) [2] introduced the SUPERB benchmark, establishing standard evaluation methodologies for speech representation learning and demonstrating "
        "that learnable layer-weighted combinations of intermediate representations consistently outperform fixed top-layer embeddings across diverse speech classification tasks. "
        "Pepino, Riera, and Ferrer (2021) [27] and Sun et al. (2024) [30] demonstrated the efficacy of fine-tuning pre-trained representations for downstream "
        "emotion recognition, while Wang and Yang (2025) [14] integrated fine-tuned Wav2vec 2.0 with neural controlled differential equation classifiers. "
        "However, recent studies by Ma et al. on emotion2vec [6] and Chen et al. on BEATs [7] demonstrate that standard speech models optimize for phonetic "
        "invariance, which can suppress emotional cues in upper transformer layers. Probing studies by Pasad, Chou, and Livescu (2021) [24] confirmed that acoustic and "
        "prosodic properties are concentrated within intermediate transformer layers, whereas final layers prioritize lexical alignment. These findings motivate "
        "the Learnable Weighted Layer Pooling approach used in this work."
    )

    add_subsec_heading("2.3 Vocal Behavioural Feature Integration")
    add_body_p(
        "Standardized acoustic parameter sets have long provided interpretable metrics for speech analysis. Eyben et al. (2016) defined the Geneva "
        "Minimalistic Acoustic Parameter Set (GeMAPS) and extended GeMAPS (eGeMAPS) [12], standardizing 88 acoustic descriptors across frequency, energy, and temporal domains. "
        "Chowdhury, Ramanna, and Kotecha (2025) [11] showed that integrating hand-crafted acoustic prosody with lightweight deep neural ensemble architectures "
        "improved diagnostic reliability and interpretability across multiple SER benchmarks."
    )

    add_subsec_heading("2.4 Speaker Disjoint Protocols and Generalization")
    add_body_p(
        "Goel, Hira, and Gupta (2024) [21] examined the challenge of unseen speaker generalization in SER, demonstrating that standard random train/test splits "
        "cause neural models to overfit speaker identity rather than true affective cues. Hashem, Arif, and Alghamdi (2023) [15] and Akçay and Oğuz (2020) [16] "
        "conducted systematic reviews detailing how cross-corpus evaluation protocols reveal severe performance degradation when models encounter novel recording environments. "
        "Wagner et al. (2018) [25] empirically evaluated hand-crafted features versus learned representations across paralinguistic tasks, finding that acoustic descriptors "
        "provide vital complementarity to deep representations, while Latif et al. (2023) [26] surveyed deep representation learning paradigms for disentangling speaker "
        "identity from affective prosody."
    )

    # --- Section 3: Dataset Ecosystem ---
    add_sec_heading("3. Dataset Ecosystem & Partitioning Protocols")
    add_body_p(
        "To ensure rigorous evaluation, five distinct corpora comprising 12,180 standardized audio files were curated, preprocessed, and partitioned: "
        "CREMA-D [17] (7,442 utterances, 91 actors), RAVDESS [18] (1,440 utterances, 24 actors), SAVEE [19] (480 utterances, 4 actors), "
        "TESS [20] (2,800 utterances, 2 actresses), and Hindi SER [1], [3] (862 utterances, 25 native speakers curated from Project Vaani, Indian TTS Emotion, and RapidOrc). "
        "Audio files were resampled to a standardized format: 16,000 Hz sampling rate, single-channel (mono), 16-bit PCM WAV, with Voice Activity "
        "Detection (VAD) silence trimming and amplitude normalization. Table 1 summarizes the dataset ecosystem."
    )

    # Table 1: Dataset Ecosystem (Centered Caption, Left Text, Center Numbers)
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
        ["CREMA-D", "7,442", "English (US)", "91 Diverse Actors", "Actor-Disjoint (13 Unseen)", "6 Classes"],
        ["RAVDESS", "1,440", "English (NA)", "24 Professional Actors", "Actor-Disjoint (4 Unseen)", "8 Classes"],
        ["SAVEE", "480", "English (UK)", "4 British Actors", "Actor-Disjoint (1 Unseen)", "7 Classes"],
        ["TESS", "2,800", "English (CA)", "2 Actresses, 200 Words", "Prompt-Disjoint (30 Words)", "7 Classes"],
        ["Hindi SER", "862", "Hindi (Indic)", "25 Native Speakers", "Disjoint Split", "5 Classes"],
        ["Total", "12,180", "Multilingual", "121+ Total Speakers", "Strict Zero Leakage", "Canonical Maps"],
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
            # Alignment: column 1 (numbers) centered, all other columns left-aligned
            if c_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

            p_run = p.runs[0]
            p_run.font.name = "Times New Roman"
            p_run.font.size = Pt(8.5)
            p_run.font.color.rgb = BLACK
            if r_idx == 0:
                p_run.font.bold = True
            elif r_idx == len(tbl1_data) - 1:
                p_run.font.bold = True
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)

    p_t1_note = doc.add_paragraph()
    p_t1_note.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_t1_note.paragraph_format.space_before = Pt(2)
    p_t1_note.paragraph_format.space_after = Pt(6)
    run_t1_note = p_t1_note.add_run(
        "*Note: Across the four English source corpora, raw clips total 12,162 (CREMA-D: 7,442; RAVDESS: 1,440; SAVEE: 480; TESS: 2,800). "
        "After standardizing onto the 6 shared canonical classes (neutral, happy, sad, angry, fear, disgust) and excluding non-shared classes "
        "(such as calm and surprise, totaling 844 clips), the English multi-corpus pool contains 11,318 audio clips. Combined with the 862 native "
        "Hindi clips (5 classes), the entire evaluation framework encompasses 12,180 standardized audio clips."
    )
    run_t1_note.font.name = "Times New Roman"
    run_t1_note.font.size = Pt(8.0)
    run_t1_note.font.italic = True
    run_t1_note.font.color.rgb = BLACK

    # --- Section 4: Methodology ---
    add_sec_heading("4. Methodology & Model Architecture")
    add_body_p(
        "The system architecture features a dual-branch processing pipeline: (1) a Neural Acoustic Classifier Branch processing audio "
        "through pre-trained self-supervised transformer backbones with learnable weighted layer pooling or CNN-BiLSTM networks, and "
        "(2) an Audio Behaviour Analysis Engine extracting continuous prosodic and temporal dynamics (F0 intonation, syllabic tempo, pause frequency, and RMS loudness)."
    )

    add_figure("fig1_system_architecture.png", "Figure 1: End-to-End System Architecture with Dual-Branch Behavioural Prosody and Neural Classification Pipeline.", width_in=6.0)

    add_subsec_heading("4.1 Learnable Weighted Layer Pooling")
    add_body_p(
        "Following the weighted layer pooling formulation established by the SUPERB benchmark (Yang et al., 2021) [2] and Pepino et al. (2021) [27], "
        "we adopt a learnable layer-wise weighted sum across all L = 12 transformer encoder representations h_t^(l) in R^D (l in {1, ..., L}):"
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
        "where W_c in R^(C x D) and b_c in R^C (with C = 6 emotion classes). "
        "With the backbone frozen, the total trainable parameters comprise only the 12 layer scalar weights and the linear probe: "
        "12 + 768 x 6 + 6 = 4,626 parameters (representing ~0.005% of the total network capacity)."
    )

    add_subsec_heading("4.2 Audio Behaviour Engine Telemetry")
    add_body_p(
        "The Behaviour Engine calculates four primary continuous acoustic descriptors: (1) Syllabic Speaking Speed (R_speech = N_syl / T_active in syllables/second), "
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
        "Models were trained using the AdamW optimizer with Cosine Annealing learning rate schedules. Transformer backbones utilized a base "
        "learning rate of 1e-5 (frozen feature extractor) and head rate of 1e-3. The CNN-BiLSTM was optimized at 5e-4 with ReduceLROnPlateau. "
        "Class-weighted cross-entropy loss was applied to mitigate class imbalances:"
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

    # --- Section 6: Results ---
    add_sec_heading("6. Benchmark Results & Comparative Analysis")

    add_subsec_heading("6.1 Universal Multi-Corpus Linear Probe Benchmark")
    add_body_p(
        "To evaluate whether a unified representation can generalize across diverse acoustic environments, accents, and recording conditions, a Universal "
        "HuBERT Model was trained on the combined 4-corpus dataset (121 speakers across CREMA-D, RAVDESS, SAVEE, and TESS) and evaluated against "
        "1,701 unseen multi-corpus test utterances.\n\n"
        "Architecturally, this model employs a frozen self-supervised HuBERT-Base backbone (94.7M parameters) coupled with our Learnable Weighted "
        "Layer Pooling module and a linear classification head. Only 4,626 parameters were trained, representing approximately 0.005% of the total network parameters. "
        "Freezing the backbone avoids catastrophic forgetting of generic acoustic representations while providing an efficient linear probe evaluation of the pre-trained "
        "features across diverse corpora. Table 2 reports the benchmark leaderboard alongside sub-cohort breakdowns on unseen test partitions."
    )

    # Table 2: Multi-Corpus Leaderboard (Centered Caption, Left Text, Center Numbers)
    p_cap2 = doc.add_paragraph()
    p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap2.paragraph_format.space_before = Pt(8)
    p_cap2.paragraph_format.space_after = Pt(2)
    p_cap2_run = p_cap2.add_run("Table 2: Universal Multi-Corpus Test Leaderboard (1,701 Unseen Clips)")
    p_cap2_run.font.name = "Times New Roman"
    p_cap2_run.font.size = Pt(9.5)
    p_cap2_run.font.bold = True
    p_cap2_run.font.color.rgb = BLACK

    tbl2_data = [
        ["Model / Evaluation Strategy", "Test Accuracy", "Macro-F1", "Test UAR", "Status / Scope"],
        ["Universal HuBERT (Frozen Transfer + Head)", "68.31%", "0.6779", "68.61%", "Unified Champion (4.1x chance)"],
        ["Zero-Shot CREMA-D HuBERT Baseline", "60.61%", "0.6031", "60.54%", "Baseline Multi-Corpus Benchmark"],
        ["Sub-Cohort: CREMA-D (1,060 clips, 13 actors)", "72.45%", "0.7232", "72.03%", "Unseen Diverse Actors (IDs 1079-1091)"],
        ["Sub-Cohort: TESS (360 clips, 30 words)", "68.89%", "0.6771", "68.89%", "Unseen Vocabulary Words"],
        ["Sub-Cohort: RAVDESS (176 clips, 4 actors)", "52.27%", "0.5018", "51.14%", "Unseen Professional Actors (21-24)"],
        ["Sub-Cohort: SAVEE (105 clips, 1 actor)", "51.43%", "0.3999", "38.10%", "Unseen British Actor (KL)"],
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
            # Alignment: column 0 left-aligned, columns 1-3 centered, column 4 left-aligned
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
            elif r_idx == 1:
                p_run.font.bold = True
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_figure("fig3_benchmark_performance.png", "Figure 2: Benchmark Accuracy and Macro-F1 across English and Hindi Speech Corpora.", width_in=5.8)

    add_subsec_heading("6.2 In-Domain Multi-Corpus Benchmark Summary")
    add_body_p(
        "Individual in-domain evaluations across all five corpora reveal consistent patterns under strict speaker-disjoint splits:"
    )

    # 4 In-Domain Evaluations: Multi-line detailed points -> JUSTIFIED
    add_bullet_point("• CREMA-D (91 Actors, 13 Unseen Test Actors): ", "Soft-Voting Top-5 Ensemble achieved 75.57% Accuracy, 0.7594 Macro-F1, and 75.61% UAR. HuBERT with Learnable Layer Pooling reached 71.98% Accuracy (0.7209 F1), outperforming Wav2Vec2 Base (69.25%) and MFCC+CNN-BiLSTM (63.30%). Wav2Vec2-XLS-R-300M (Frozen Baseline) reached only 24.43% Accuracy (near chance level of 16.67%).", justify=True)
    add_bullet_point("• RAVDESS (24 Actors, Actors 21 to 24 Unseen): ", "Transfer Ensemble achieved 73.75% Accuracy, 0.7207 Macro-F1, and 72.27% UAR. Transfer from CREMA-D pre-training to RAVDESS produced 72.92% Accuracy, compared to 32.50% when trained from scratch using HuBERT alone. Wav2Vec2-XLS-R-300M collapsed to 13.33% Accuracy (barely above chance level of 12.50%).", justify=True)
    add_bullet_point("• SAVEE (4 Actors, Actor KL Unseen): ", "Transfer ensemble reached 51.67% Accuracy, 0.3860 Macro-F1, and 40.48% UAR, substantially surpassing the HuBERT scratch baseline of 25.83% (0.0795 F1) which suffered from vocal tract overfitting. Note: In-domain SAVEE evaluation is conducted on a single unseen British actor (Actor KL, 120 clips), introducing higher empirical variance.", justify=True)
    add_bullet_point("• TESS (2 Actresses, 200 Words, 30 Unseen Target Words): ", "All in-domain SSL foundation models achieved 100.00% Accuracy and 1.0000 Macro-F1 on prompt-independent splits. When evaluated zero-shot with the multi-corpus Universal HuBERT model, TESS performance settles at 68.89%, illustrating that the 100% in-domain score reflects the constrained acoustic complexity of the two-speaker studio recording rather than infinite generalization.", justify=True)

    # Table 3: In-Domain Benchmark Leaderboard (Centered Caption, Left Text, Center Numbers)
    p_cap3 = doc.add_paragraph()
    p_cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap3.paragraph_format.space_before = Pt(8)
    p_cap3.paragraph_format.space_after = Pt(2)
    p_cap3_run = p_cap3.add_run("Table 3: In-Domain Benchmark Leaderboard Across 5 Evaluated Corpora")
    p_cap3_run.font.name = "Times New Roman"
    p_cap3_run.font.size = Pt(9.5)
    p_cap3_run.font.bold = True
    p_cap3_run.font.color.rgb = BLACK

    tbl3_data = [
        ["Dataset", "Best Model", "Accuracy", "Macro-F1", "UAR", "Chance"],
        ["CREMA-D", "Top-5 Soft-Voting Ensemble", "75.57%", "0.7594", "75.61%", "16.67%"],
        ["RAVDESS", "Transfer Ensemble (CREMA-D)", "73.75%", "0.7207", "72.27%", "12.50%"],
        ["SAVEE", "Transfer Ensemble (CREMA-D)", "51.67%", "0.3860", "40.48%", "14.29%"],
        ["TESS", "TESS-only HuBERT / W2V2", "100.00%", "1.0000", "100.00%", "14.29%"],
        ["Hindi SER", "CNN-BiLSTM Specialist", "74.42%", "0.7201", "70.85%", "20.00%"],
        ["Hindi SER", "Top-2 Ensemble (CNN-BiLSTM + LSTM)", "75.19%", "0.7136", "70.56%", "20.00%"],
        ["Combined", "Universal HuBERT (Frozen)", "68.31%", "0.6779", "68.61%", "16.67%"],
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
            # Alignment: columns 0 and 1 left-aligned, columns 2-5 centered
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
        "*Note: In the experimental benchmarking configs, emotion2vec+ was evaluated using the facebook/wav2vec2-base proxy architecture "
        "and BEATs using microsoft/wavlm-base-plus under the unified 768-dimensional transformer feature extraction interface. "
        "All transformer backbones are Base variants (768 hidden dimensions). On SAVEE, the single-speaker test set (Actor KL) exhibits "
        "higher variance than multi-speaker test cohorts."
    )
    run_t3_note.font.name = "Times New Roman"
    run_t3_note.font.size = Pt(8.0)
    run_t3_note.font.italic = True
    run_t3_note.font.color.rgb = BLACK

    add_subsec_heading("6.3 Technical Analysis of Wav2Vec2-XLS-R-300M Failure")
    add_body_p(
        "Across all evaluated corpora, Wav2Vec2-XLS-R-300M [10] performed near random chance (13.33% on RAVDESS, 24.43% on CREMA-D, 12.50% on SAVEE, "
        "and 19.76% on TESS), underperforming even shallow MFCC baselines. Three primary technical factors explain this behavior:"
    )

    # 3 Technical Factors: Multi-line detailed explanations -> JUSTIFIED
    add_bullet_point("1. ASR Invariant Pre-training Objective: ", "XLS-R-300M was pre-trained across 128 languages using contrastive masked prediction to extract phonetic content. In cross-lingual speech recognition, speaker-specific pitch variations and emotional intonations are treated as nuisance parameters and filtered out to achieve cross-lingual phonetic invariance. Consequently, the frozen representations suppress paralinguistic and affective cues.", justify=True)
    add_bullet_point("2. Top-Layer Emotional Depletion: ", "Unlike our HuBERT framework which incorporates learnable layer pooling across intermediate depths, the frozen XLS-R baseline extracted features exclusively from its 24th (final) layer. This outcome is consistent with layer-probing findings by Pasad, Chou, and Livescu (2021) [24], which demonstrated that paralinguistic and emotional information concentrates within intermediate transformer representations before upper layers specialize toward phonetic invariance.", justify=True)
    add_bullet_point("3. Capacity-to-Sample Mismatch: ", "Projecting a frozen 1024-dimensional representation from a 317M-parameter model onto tiny target datasets (e.g., 384 SAVEE clips or 960 RAVDESS clips) without layer-wise adaptation or fine-tuning creates an acute representation mismatch that prevents effective linear separation.", justify=True)

    # --- Section 7: Ablation Studies ---
    add_sec_heading("7. Empirical Findings & Ablation Studies")

    add_subsec_heading("7.1 The Speaker Diversity Effect")
    add_body_p(
        "Comparing performance across SAVEE (3 training actors), RAVDESS (20 training actors), and CREMA-D (78 training actors) demonstrates a consistent "
        "relationship between speaker cohort size and generalization capability on strictly unseen test speakers. Evaluating HuBERT models trained from "
        "scratch across these datasets reveals that on SAVEE (3 training speakers), HuBERT achieved only 25.83% test accuracy (Macro-F1 0.0795) due to vocal tract "
        "overfitting on the limited speaker cohort. Expanding the training cohort to 20 actors in RAVDESS elevated scratch HuBERT accuracy to 32.50% (and 68.75% for the "
        "scratch ensemble). In CREMA-D, with 78 training actors, HuBERT from scratch reached 71.98% accuracy (and 75.57% for the ensemble). This empirical gradient "
        "confirms the Speaker Diversity Law: pre-training across broad multi-speaker cohorts is critical for neural models to disentangle emotional prosody "
        "from individual speaker vocal tract geometry."
    )

    add_figure("fig2_layer_weights.png", "Figure 3: Empirical Layer Weight Distribution in Learnable Weighted Layer Pooling (Layers 9 to 11 account for 31.95%, total sum = 100.00%).", width_in=5.8)

    add_subsec_heading("7.2 Layer Weight Distribution Across Transformer Depth")
    add_body_p(
        "Figure 3 illustrates the learned softmax weights alpha across the 12 transformer encoder blocks of the Universal HuBERT model:"
    )

    # 5 Layer Depth Zones: Multi-line detailed explanations -> JUSTIFIED
    add_bullet_point("• Early Layers (Layers 1 to 4): ", "Weights remain basal (alpha_1 = 0.0707, alpha_2 = 0.0710, alpha_3 = 0.0711, alpha_4 = 0.0712, representing 7.07% to 7.12%), capturing low-level spectro-temporal acoustics.", justify=True)
    add_bullet_point("• Intermediate Transition (Layers 5 to 8): ", "Weights steadily increase (alpha_5 = 0.0713, alpha_6 = 0.0717, alpha_7 = 0.0725, alpha_8 = 0.0757, representing 7.13% to 7.57%), reflecting progressive harmonic abstraction.", justify=True)
    add_bullet_point("• Prosodic Culmination Zone (Layers 9 to 11): ", "Weights reach their empirical maximum (alpha_9 = 0.1002, alpha_10 = 0.1107, alpha_11 = 0.1086), accounting for exactly 31.95% of the total network weight. Layer 10 serves as the primary focal point (alpha_10 = 11.07%), capturing pitch inflection contours and macro-energy modulations.", justify=True)
    add_bullet_point("• Final Layer (Layer 12): ", "Weight decreases to alpha_12 = 0.1053 (10.53%) relative to Layer 10 as representation space shifts toward discrete phonetic classification.", justify=True)
    add_bullet_point("• Normalization Verification: ", "The complete 12-layer softmax distribution (7.07% + 7.10% + 7.11% + 7.12% + 7.13% + 7.17% + 7.25% + 7.57% + 10.02% + 11.07% + 10.86% + 10.53%) sums strictly to 100.00% (sum_{i=1}^{12} alpha_i = 1.0000). Table 4 details the layer weights.", justify=True)

    # Table 4: Layer Weights (Centered Caption, Left Text, Center Numbers)
    p_cap4 = doc.add_paragraph()
    p_cap4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap4.paragraph_format.space_before = Pt(8)
    p_cap4.paragraph_format.space_after = Pt(2)
    p_cap4_run = p_cap4.add_run("Table 4: Layer-Wise Softmax Attention Weight Distribution (HuBERT-Base)")
    p_cap4_run.font.name = "Times New Roman"
    p_cap4_run.font.size = Pt(9.5)
    p_cap4_run.font.bold = True
    p_cap4_run.font.color.rgb = BLACK

    tbl4_data = [
        ["Layer Index", "Softmax Weight", "Percentage", "Functional Acoustic Role"],
        ["Layer 1", "0.0707", "7.07%", "Waveform envelope & low-level spectral energy"],
        ["Layer 2", "0.0710", "7.10%", "Formant structures and spectral slope"],
        ["Layer 3", "0.0711", "7.11%", "Pitch frequency baseline estimation"],
        ["Layer 4", "0.0712", "7.12%", "Spectral flux and voice onset timing"],
        ["Layer 5", "0.0713", "7.13%", "Phonetic-prosodic transition boundary"],
        ["Layer 6", "0.0717", "7.17%", "Intermediate harmonic structure encoding"],
        ["Layer 7", "0.0725", "7.25%", "Broad phonetic category separation"],
        ["Layer 8", "0.0757", "7.57%", "Prosodic phrasing & cadence abstraction"],
        ["Layer 9", "0.1002", "10.02%", "Emotional inflection & macro-prosody onset"],
        ["Layer 10", "0.1107", "11.07%", "Peak affective salience & intonation contours"],
        ["Layer 11", "0.1086", "10.86%", "Global utterance affect & speaker dynamics"],
        ["Layer 12", "0.1053", "10.53%", "Phonetic discrimination & lexical alignment"],
        ["Total Sum", "1.0000", "100.00%", "Strict mathematical normalization verified"],
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
            # Alignment: columns 0 and 3 left-aligned, columns 1 and 2 centered
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
            elif r_idx in [9, 10, 11]:  # Highlight intermediate prosodic layers
                p_run.font.bold = True
            elif r_idx == len(tbl4_data) - 1:
                p_run.font.bold = True
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_subsec_heading("7.3 Cross-Lingual Adaptation to Indic Hindi Speech")
    add_body_p(
        "Evaluating the English-trained Universal HuBERT model zero-shot on the native Hindi test split yielded 27.62% accuracy and 31.76% UAR "
        "(exceeding the 20.00% 5-class random chance baseline). While cross-lingual transfer occurred, linguistic differences limited precision. "
        "Supervised training of the specialized CNN-BiLSTM architecture directly on the Hindi training split achieved 74.42% test accuracy, "
        "0.7201 Macro-F1, and 70.85% UAR (with the Top-2 ensemble of CNN-BiLSTM + LSTM reaching 75.19% accuracy and 70.56% UAR). This represents "
        "an absolute improvement of 46.80 percentage points (47.57 points for the ensemble) over zero-shot transfer. "
        "Figure 4 illustrates this comparison, and Figure 5 displays the corresponding normalized confusion matrix."
    )

    add_figure("fig4_cross_lingual_transfer.png", "Figure 4: Cross-Lingual Adaptation to Indic Hindi Speech (Zero-Shot vs. Supervised Adaptation).", width_in=5.8)
    add_figure("fig5_hindi_confusion_matrix.png", "Figure 5: Normalized Confusion Matrix for the Hindi Emotion Specialist Model.", width_in=4.8)

    # --- Section 8: Behavioural Telemetry ---
    add_sec_heading("8. Speech Behavioural Intelligence Profiling")
    add_body_p(
        "Figure 6 summarizes the objective acoustic patterns extracted across emotion categories by the Behaviour Engine:"
    )

    # 4 Emotion Behaviour Profiles: Multi-line detailed profiles -> JUSTIFIED
    add_bullet_point("• Anger: ", "Characterized by an accelerated speaking tempo (mean 4.2 syl/s), minimal hesitation (pause ratio 12.4%), high vocal intensity (mean loudness -16.2 dB), and sharp pitch variance (sigma_F0 = 54.3 Hz).", justify=True)
    add_bullet_point("• Sadness: ", "Exhibits psychomotor deceleration with a slow speaking tempo (mean 2.2 syl/s), extensive silence intervals (pause ratio 31.8%), attenuated energy (mean loudness -29.4 dB), and flat fundamental frequency intonation (mean pitch 108.4 Hz, sigma_F0 = 18.2 Hz).", justify=True)
    add_bullet_point("• Joy: ", "Features elevated pitch dynamics (mean pitch 232.1 Hz, sigma_F0 = 62.1 Hz) and moderate tempo (3.6 syl/s).", justify=True)
    add_bullet_point("• Neutral / Calm: ", "Displays balanced cadence (2.8 to 3.4 syl/s), standard pause ratio (18% to 22%), and stable loudness (-22 to -26 dB).", justify=True)

    add_figure("fig6_behavioral_prosody_profile.png", "Figure 6: Multimodal Speech Behaviour Telemetry across Discrete Emotion Categories.", width_in=6.0)

    # --- Section 9: Deployment Architecture ---
    add_sec_heading("9. System Deployment Architecture")
    add_body_p(
        "The end-to-end framework is implemented as an Apple Silicon accelerated microservice paired with a minimal web application:"
    )

    # 2 Deployment Components: Multi-line detailed descriptions -> JUSTIFIED
    add_bullet_point("• Frontend UI (Next.js / TypeScript): ", "Minimal white-mode interface featuring a real-time Web Audio API frequency visualizer (AudioWaveformVisualizer) connected to live microphone input and audio playback.", justify=True)
    add_bullet_point("• Backend Microservice (FastAPI): ", "Model registry serving the Hindi Specialist (CNN-BiLSTM) and Universal SER models with hardware acceleration, achieving 19.9 ms inference latency per clip for the lightweight CNN-BiLSTM specialist and 191.4 ms for the 12-layer Universal HuBERT model.", justify=True)

    # --- Section 10: Discussion ---
    add_sec_heading("10. Discussion & Limitations")
    add_body_p(
        "While the experimental results validate the efficacy of learnable layer pooling and disjoint evaluation protocols, several limitations should be noted:"
    )

    # 3 Limitations: Multi-line detailed points -> JUSTIFIED
    add_bullet_point("1. Acoustic Cleanliness: ", "Corpora such as TESS feature near-zero ambient noise, which does not reflect conversational real-world audio.", justify=True)
    add_bullet_point("2. Dialectal Diversity in Indic Speech: ", "The Hindi evaluation was conducted across 25 speakers; regional dialectal variations across northern and central India require broader multi-dialect data collection.", justify=True)
    add_bullet_point("3. Pre-trained Audio Sampling: ", "Standard foundation models operate at 16 kHz, which truncates ultra-high frequency acoustic cues (> 8 kHz).", justify=True)

    # --- Section 11: Conclusion ---
    add_sec_heading("11. Conclusion")
    add_body_p(
        "This research evaluated speech emotion recognition across multi-corpus and cross-lingual settings. The primary conclusions are:"
    )

    # 4 Conclusions: Multi-line detailed conclusions -> JUSTIFIED
    add_bullet_point("1. Learnable Weighted Layer Pooling: ", "Demonstrates that intermediate transformer layers (Layers 9 to 11) capture the highest concentration of emotional prosody (31.95%), retaining stronger affective salience than early acoustic representations.", justify=True)
    add_bullet_point("2. Speaker Diversity: ", "Essential for generalization: models trained on minimal speaker cohorts overfit speaker identity, whereas pre-training across larger cohorts supports speaker-independent evaluation.", justify=True)
    add_bullet_point("3. Cross-Lingual Transfer: ", "English pre-trained models transfer moderately above chance (27.62% vs. 20.00% floor) to native Hindi speech, but supervised adaptation using specialized CNN-BiLSTM networks achieves 74.42% accuracy (75.19% via ensemble fusion).", justify=True)
    add_bullet_point("4. Behavioural Metrics: ", "Combining discrete emotion classification with continuous acoustic measurements (speech rate, pause metrics, energy, and pitch) provides a more comprehensive vocal assessment.", justify=True)

    # --- Section: References (LEFT-ALIGNED to avoid ugly justified gaps in citations) ---
    add_sec_heading("References")

    references = [
        '[1] S. Kotian and S. Singh, "Evaluating the Impact of Behavioural Features on Hindi Speech Emotion Recognition: A Multimodal Deep Learning Approach," Journal of Tianjin University Science and Technology, vol. 59, no. 2, pp. 147–165, Feb. 2026, doi: 10.5281/zenodo.18797014.',
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
        '[30] C. Sun, Y. Zhou, X. Huang, J. Yang, and X. Hou, "Combining wav2vec 2.0 Fine-Tuning and ConLearnNet for Speech Emotion Recognition," Electronics, vol. 13, no. 6, art. 1103, pp. 1–19, Mar. 2024, doi: 10.3390/electronics13061103.'
    ]

    for ref in references:
        rp = doc.add_paragraph()
        rp.alignment = WD_ALIGN_PARAGRAPH.LEFT  # Strict left alignment prevents awkward spacing gaps in citations
        rp.paragraph_format.left_indent = Inches(0.25)
        rp.paragraph_format.first_line_indent = Inches(-0.25)  # Hanging indent
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
