"""
Apply final scientific precision edits:
1. Update Figure 3 caption in scripts/generate_docx_latex_styled.py:
   Remove 'total sum = 100.00%', state unrounded ~31.95% and exported sum 99.99%.
2. Replace unverified demographic assertion 'native speakers' / 'native Hindi' with
   'Hindi speakers' / 'Hindi speech utterances' / 'in-domain adaptation'.
3. Harmonize figure labels in scripts/generate_report_figures.py.
4. Regenerate figures and both Word document deliverables.
"""

from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCX_SCRIPT = PROJECT_ROOT / "scripts" / "generate_docx_latex_styled.py"
FIG_SCRIPT = PROJECT_ROOT / "scripts" / "generate_report_figures.py"

def update_figures_script():
    with open(FIG_SCRIPT, "r", encoding="utf-8") as f:
        code = f.read()

    replacements = [
        ('ax.text(0.455, 0.71, "Hindi Specialist\\n(Native Supervised)",', 'ax.text(0.455, 0.71, "Hindi Specialist\\n(In-Domain Supervised)",'),
        ('corpora = ["CREMA-D\\n(91 Actors)", "RAVDESS\\n(24 Actors)", "SAVEE\\n(4 Actors)", "TESS\\n(200 Words)", "Hindi SER\\n(Native Ind.)", "Multi-Corpus\\n(1,701 Unseen)"]',
         'corpora = ["CREMA-D\\n(91 Actors)", "RAVDESS\\n(24 Actors)", "SAVEE\\n(4 Actors)", "TESS\\n(200 Words)", "Hindi SER\\n(Indic 14 Spk)", "Multi-Corpus\\n(1,701 Unseen)"]'),
        ('categories = ["Zero-Shot Transfer\\n(English HuBERT -> Hindi)", "Native Supervised\\n(Hindi Ensemble)"]',
         'categories = ["Zero-Shot Transfer\\n(English HuBERT -> Hindi)", "In-Domain Supervised\\n(Hindi Ensemble)"]'),
        ('ax.annotate("+47.57% Accuracy Gain\\nVia Native In-Domain Supervision",',
         'ax.annotate("+47.57% Accuracy Gain\\nVia In-Domain Supervision",'),
    ]

    for old, new in replacements:
        if old in code:
            code = code.replace(old, new, 1)

    with open(FIG_SCRIPT, "w", encoding="utf-8") as f:
        f.write(code)

    print("Updated scripts/generate_report_figures.py successfully.")
    return True


def update_docx_script():
    with open(DOCX_SCRIPT, "r", encoding="utf-8") as f:
        code = f.read()

    replacements = [
        # Subtitle
        (
            '"A Controlled Empirical Evaluation Across CREMA-D, RAVDESS, SAVEE, TESS, and Native Hindi Speech"',
            '"A Controlled Empirical Evaluation Across CREMA-D, RAVDESS, SAVEE, TESS, and Indic Hindi Speech"'
        ),
        # Abstract: Hindi utterances
        (
            '"and (2) a cross-lingual transfer and native adaptation study on an Indic speech corpus (862 standardized Hindi utterances across 14 unique speaker IDs "',
            '"and (2) a cross-lingual transfer and in-domain adaptation study on an Indic speech corpus (862 standardized Hindi speech utterances across 14 unique speaker IDs "'
        ),
        # Abstract: canonical subset
        (
            '"evaluation of the English foundation model on the shared canonical subset of native Hindi speech yields 27.62% accuracy and 31.76% Unweighted Average Recall "',
            '"evaluation of the English foundation model on the shared canonical subset of Hindi speech yields 27.62% accuracy and 31.76% Unweighted Average Recall "'
        ),
        # RQ3
        (
            'add_bullet_point("• RQ3 (Cross-Lingual Transfer to Indic Speech): ", "To what degree do English multi-corpus representations transfer zero-shot to native Hindi speech, and what quantitative performance gain is achieved via native supervised adaptation?", justify=True)',
            'add_bullet_point("• RQ3 (Cross-Lingual Transfer to Indic Speech): ", "To what degree do English multi-corpus representations transfer zero-shot to Hindi speech, and what quantitative performance gain is achieved via supervised in-domain adaptation?", justify=True)'
        ),
        # Literature survey
        (
            'weights, and quantifies both zero-shot cross-lingual transfer and native adaptation on Hindi speech.',
            'weights, and quantifies both zero-shot cross-lingual transfer and supervised in-domain adaptation on Hindi speech.'
        ),
        # Dataset note 1
        (
            'Combined with the 862 native Hindi clips (5 classes), the complete evaluation encompasses 12,180 audio clips.',
            'Combined with the 862 standardized Hindi clips (5 classes), the complete evaluation encompasses 12,180 audio clips.'
        ),
        # Figure 3 Caption fix
        (
            'add_figure("fig2_layer_weights.png", "Figure 3: Empirical Layer Weight Distribution in Learnable Weighted Layer Pooling (Layers 9 to 11 receive 31.95%, total sum = 100.00%).", width_in=5.8)',
            'add_figure("fig2_layer_weights.png", "Figure 3: Empirical Layer Weight Distribution in Learnable Weighted Layer Pooling. Layers 9–11 receive approximately 31.95% of the unrounded normalized weight; exported four-decimal values sum to 99.99% due to rounding.", width_in=5.8)'
        ),
        # Conclusion bullet 3
        (
            'add_bullet_point("3. Cross-Lingual Transfer & Supervised Adaptation: ", "English pre-trained models transfer moderately above chance (27.62% vs. 25.00% floor) to native Hindi speech, but supervised adaptation using specialized CNN-BiLSTM networks achieves 74.42% accuracy (75.19% via ensemble fusion), representing a +46.80% single-model performance gain.", justify=True)',
            'add_bullet_point("3. Cross-Lingual Transfer & Supervised Adaptation: ", "English pre-trained models transfer moderately above chance (27.62% vs. 25.00% floor) to Hindi speech, but supervised adaptation using specialized CNN-BiLSTM networks achieves 74.42% accuracy (75.19% via ensemble fusion), representing a +46.80% single-model performance gain.", justify=True)'
        ),
    ]

    for idx, (old, new) in enumerate(replacements, 1):
        if old in code:
            code = code.replace(old, new, 1)
            print(f"Replacement #{idx} succeeded in docx script.")
        else:
            print(f"Replacement #{idx} skipped (already applied or not found): {old[:50]}")

    with open(DOCX_SCRIPT, "w", encoding="utf-8") as f:
        f.write(code)

    print("Updated scripts/generate_docx_latex_styled.py successfully.")
    return True


def main():
    if not update_figures_script():
        return
    if not update_docx_script():
        return

    print("Regenerating figures...")
    res_fig = subprocess.run([str(PROJECT_ROOT / ".venv" / "bin" / "python"), str(FIG_SCRIPT)], capture_output=True, text=True)
    print(res_fig.stdout)
    if res_fig.returncode != 0:
        print("Figure generation error:", res_fig.stderr)
        return

    print("Regenerating Word document deliverables...")
    res_docx = subprocess.run([str(PROJECT_ROOT / ".venv" / "bin" / "python"), str(DOCX_SCRIPT)], capture_output=True, text=True)
    print(res_docx.stdout)
    if res_docx.returncode != 0:
        print("Docx generation error:", res_docx.stderr)
        return

    print("All tasks completed successfully!")

if __name__ == "__main__":
    main()
