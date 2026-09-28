"""
Apply submission-level precision fixes:
1. Update '121 speakers' in Universal training set description to 103 unique training speaker IDs.
2. Soften conclusion claim on layer pooling in docx and markdown reports.
3. Update README.md to clearly specify partition protocols (speaker-disjoint vs prompt-disjoint vs stratified utterance-level).
4. Regenerate FINAL_RESEARCH_REPORT.docx and FINAL_RESEARCH_REPORT.md.
"""

from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCX_SCRIPT = PROJECT_ROOT / "scripts" / "generate_docx_latex_styled.py"
MD_SCRIPT = PROJECT_ROOT / "scripts" / "generate_markdown_report.py"
README_PATH = PROJECT_ROOT / "README.md"

def update_docx_script():
    with open(DOCX_SCRIPT, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. 103 training speaker IDs
    old_hubert_text = (
        '        "HuBERT probe was initialized from the best CREMA-D HuBERT checkpoint (outputs/cremad/hubert/checkpoints/best_model/model.pt, logged as HuBERT "\n'
        '        "(Transfer from CREMAD)) and subsequently adapted on the combined 4-corpus training set (121 speakers across CREMA-D, RAVDESS, SAVEE, and TESS) "\n'
        '        "and evaluated against 1,701 unseen multi-corpus test utterances (1,060 CREMA-D + 360 TESS + 176 RAVDESS + 105 SAVEE).\\n\\n"'
    )
    new_hubert_text = (
        '        "HuBERT probe was initialized from the best CREMA-D HuBERT checkpoint (outputs/cremad/hubert/checkpoints/best_model/model.pt, logged as HuBERT "\n'
        '        "(Transfer from CREMAD)) and subsequently adapted on the combined four-corpus training set, comprising 103 unique training speaker IDs across "\n'
        '        "CREMA-D, RAVDESS, SAVEE, and TESS (TESS uses prompt-disjoint rather than speaker-disjoint evaluation), and evaluated against 1,701 unseen "\n'
        '        "multi-corpus test utterances (1,060 CREMA-D + 360 TESS + 176 RAVDESS + 105 SAVEE).\\n\\n"'
    )

    # 2. Conclusion point 1
    old_conc_text = (
        '    add_bullet_point("1. Learnable Weighted Layer Pooling: ", "The learned pooling mechanism assigned its highest aggregate weight to Layers 9–11, which together received 31.95% of the normalized layer weight, demonstrating that intermediate transformer representations provide superior affective utility compared to early acoustic layers.", justify=True)'
    )
    new_conc_text = (
        '    add_bullet_point("1. Learnable Weighted Layer Pooling: ", "The learned pooling mechanism assigned its highest aggregate weight to Layers 9–11, which together received approximately 31.95% of the normalized layer weight. This indicates that the downstream probe preferentially weighted these intermediate representations under the evaluated multi-corpus protocol.", justify=True)'
    )

    if old_hubert_text not in code:
        print("Error: old_hubert_text not found in docx script!")
        return False
    code = code.replace(old_hubert_text, new_hubert_text, 1)

    if old_conc_text not in code:
        print("Error: old_conc_text not found in docx script!")
        return False
    code = code.replace(old_conc_text, new_conc_text, 1)

    with open(DOCX_SCRIPT, "w", encoding="utf-8") as f:
        f.write(code)

    print("Updated scripts/generate_docx_latex_styled.py successfully.")
    return True


def update_md_script():
    with open(MD_SCRIPT, "r", encoding="utf-8") as f:
        code = f.read()

    old_hubert_md = (
        "To evaluate whether a unified representation can generalize across diverse acoustic environments, accents, and recording conditions, a Universal HuBERT probe was initialized from the best CREMA-D HuBERT checkpoint (`outputs/cremad/hubert/checkpoints/best_model/model.pt`, logged as `HuBERT (Transfer from CREMAD)`) and subsequently adapted on the combined 4-corpus training set (121 speakers across CREMA-D, RAVDESS, SAVEE, and TESS) and evaluated against 1,701 unseen multi-corpus test utterances (1,060 CREMA-D + 360 TESS + 176 RAVDESS + 105 SAVEE)."
    )
    new_hubert_md = (
        "To evaluate whether a unified representation can generalize across diverse acoustic environments, accents, and recording conditions, a Universal HuBERT probe was initialized from the best CREMA-D HuBERT checkpoint (`outputs/cremad/hubert/checkpoints/best_model/model.pt`, logged as `HuBERT (Transfer from CREMAD)`) and subsequently adapted on the combined four-corpus training set, comprising 103 unique training speaker IDs across CREMA-D, RAVDESS, SAVEE, and TESS (TESS uses prompt-disjoint rather than speaker-disjoint evaluation), and evaluated against 1,701 unseen multi-corpus test utterances (1,060 CREMA-D + 360 TESS + 176 RAVDESS + 105 SAVEE)."
    )

    old_conc_md = (
        "1. **Learnable Weighted Layer Pooling:** The learned pooling mechanism assigned its highest aggregate weight to Layers 9–11, which together received approximately 31.95% of the normalized layer weight (31.94% exported 4-decimal rounded sum), demonstrating that intermediate transformer representations provide superior affective utility compared to early acoustic layers."
    )
    new_conc_md = (
        "1. **Learnable Weighted Layer Pooling:** The learned pooling mechanism assigned its highest aggregate weight to Layers 9–11, which together received approximately 31.95% of the normalized layer weight. This indicates that the downstream probe preferentially weighted these intermediate representations under the evaluated multi-corpus protocol."
    )

    if old_hubert_md not in code:
        print("Error: old_hubert_md not found in md script!")
        return False
    code = code.replace(old_hubert_md, new_hubert_md, 1)

    if old_conc_md not in code:
        print("Error: old_conc_md not found in md script!")
        return False
    code = code.replace(old_conc_md, new_conc_md, 1)

    with open(MD_SCRIPT, "w", encoding="utf-8") as f:
        f.write(code)

    print("Updated scripts/generate_markdown_report.py successfully.")
    return True


def update_readme():
    with open(README_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    # Replace preamble line 15
    old_p15 = (
        "totaling **12,180 audio clips** under strict speaker-independent and prompt-independent evaluation protocols."
    )
    new_p15 = (
        "totaling **12,180 audio clips** under disciplined evaluation protocols: CREMA-D, RAVDESS, and SAVEE enforce speaker-disjoint test partitions; TESS enforces prompt-disjoint evaluation on unseen vocabulary; and the Hindi specialist uses a stratified utterance-level split in which speaker IDs may occur across partitions."
    )

    # Replace guarantee box
    old_guarantee = (
        "> **Strict Zero-Leakage Benchmark Guarantee**: All evaluation metrics reported herein are generated exclusively on completely unseen human actors (CREMA-D: 13 unseen actors; RAVDESS: Actors 21-24; SAVEE: Actor `KL`) or unseen vocabulary prompts (TESS: 30 unseen words). There is zero data or identity overlap between train, validation, and test partitions."
    )
    new_guarantee = (
        "> **Evaluation & Partitioning Protocols**: Evaluation metrics reported herein are generated under disciplined, clearly documented protocols: CREMA-D, RAVDESS, and SAVEE enforce strictly speaker-disjoint test partitions on unseen actors (CREMA-D: 13 unseen actors; RAVDESS: Actors 21-24; SAVEE: Actor `KL`); TESS enforces prompt-disjoint evaluation across 30 unseen vocabulary words; and the Hindi specialist is evaluated on an utterance-level stratified split (604 train / 129 val / 129 test across 14 unique speaker IDs)."
    )

    # Replace section line 145
    old_l145 = (
        "All evaluations are conducted strictly on **unseen actors or unseen prompts** (disjoint test partitions with zero leakage)."
    )
    new_l145 = (
        "All multi-corpus evaluations are conducted strictly on **unseen actors or unseen prompts** (speaker-disjoint for CREMA-D/RAVDESS/SAVEE; prompt-disjoint for TESS)."
    )

    # Replace line 149
    old_l149 = (
        "*Unified corpus of **11,318 audio clips** across 121 speakers mapped to 6 canonical emotions (`neutral`, `happy`, `sad`, `angry`, `fear`, `disgust`). Evaluated on **1,701 strictly unseen clips** across all 4 datasets simultaneously. Random chance baseline: **16.67%**.*"
    )
    new_l149 = (
        "*Unified English corpus of **11,318 audio clips** (121 total speakers across all splits; 103 unique training speaker IDs) mapped to 6 canonical emotions (`neutral`, `happy`, `sad`, `angry`, `fear`, `disgust`). Evaluated on **1,701 pooled test clips** across all 4 datasets simultaneously. Random chance baseline: **16.67%**.*"
    )

    # Replace section 637-640
    old_guar_list = (
        "1. **Strict Zero-Leakage Partitions**:\n"
        "   - **Speaker-Independent**: Test partitions for CREMA-D, RAVDESS, and SAVEE feature actors who never appear in training or validation splits.\n"
        "   - **Prompt-Independent**: Test partitions for TESS feature 30 vocabulary words never spoken in the training split."
    )
    new_guar_list = (
        "1. **Rigorous Partition Protocols**:\n"
        "   - **Speaker-Disjoint**: Test partitions for CREMA-D, RAVDESS, and SAVEE feature actors who never appear in training or validation splits.\n"
        "   - **Prompt-Disjoint**: Test partitions for TESS feature 30 vocabulary words never spoken in the training split.\n"
        "   - **Stratified Utterance-Level**: The Hindi specialist partition stratifies clips by emotion class (604 train / 129 val / 129 test), with the 14 speaker IDs distributed across partitions."
    )

    for old, new in [
        (old_p15, new_p15),
        (old_guarantee, new_guarantee),
        (old_l145, new_l145),
        (old_l149, new_l149),
        (old_guar_list, new_guar_list),
    ]:
        if old not in code:
            print(f"Warning: README target not found: {old[:50]}")
            return False
        code = code.replace(old, new, 1)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(code)

    print("Updated README.md successfully.")
    return True


def main():
    if not update_docx_script():
        return
    if not update_md_script():
        return
    if not update_readme():
        return

    print("Recompiling Word document...")
    res_docx = subprocess.run([str(PROJECT_ROOT / ".venv" / "bin" / "python"), str(DOCX_SCRIPT)], capture_output=True, text=True)
    print(res_docx.stdout)
    if res_docx.returncode != 0:
        print("Docx generation error:", res_docx.stderr)
        return

    print("Recompiling Markdown report...")
    res_md = subprocess.run([str(PROJECT_ROOT / ".venv" / "bin" / "python"), str(MD_SCRIPT)], capture_output=True, text=True)
    print(res_md.stdout)
    if res_md.returncode != 0:
        print("MD generation error:", res_md.stderr)
        return

    print("All final submission fixes applied cleanly!")

if __name__ == "__main__":
    main()
