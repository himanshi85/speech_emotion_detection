#!/usr/bin/env python3
"""
Speech Emotion Recognition & Audio Behaviour Intelligence WebUI
================================================================
Interactive web application powered by Gradio:
1. Emotion Classification & Confidence Gauges.
2. Complete Audio Behaviour Analysis Report:
   - Speaking Speed (syllables/second & words/minute)
   - Pause Frequency (pauses/minute & silence ratio)
   - Vocal Energy (dB RMS loudness)
   - Pitch Variation & Intonation (F0 mean & standard deviation)
   - Overall Speaker Behaviour Diagnosis
3. Live Microphone Recording & Audio File Upload (.wav, .mp3, .ogg).
4. Multi-Language Support (English, Hindi, and Indian Accents).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import gradio as gr
import numpy as np
import soundfile as sf
import torch

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ser.core.config import load_model_config
from ser.features.behavior import analyze_audio_file
from ser.training.trainer import load_checkpoint_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("webui")

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))

# Model registry paths
MODEL_CHECKPOINTS = {
    "Universal HuBERT (11,318 clips, Multi-Corpus)": (
        PROJECT_ROOT / "outputs" / "combined" / "universal_hubert_weighted_frozen" / "checkpoints" / "best_model" / "model.pt"
    ),
    "CREMA-D HuBERT (7,442 clips, Single-Model Champion)": (
        PROJECT_ROOT / "outputs" / "cremad" / "hubert" / "checkpoints" / "best_model" / "model.pt"
    ),
    "RAVDESS Transfer HuBERT (Weighted Layer Pooling)": (
        PROJECT_ROOT / "outputs" / "ravdess_enhanced" / "hubert_transfer_cremad_weighted" / "checkpoints" / "best_model" / "model.pt"
    ),
}

# Cache loaded models
LOADED_MODELS: Dict[str, Tuple[torch.nn.Module, Dict[str, Any], Dict[str, int]]] = {}


def get_model(model_name: str) -> Tuple[Optional[torch.nn.Module], Optional[Dict[str, Any]], Optional[Dict[str, int]]]:
    if model_name in LOADED_MODELS:
        return LOADED_MODELS[model_name]

    ckpt_path = MODEL_CHECKPOINTS.get(model_name)
    if ckpt_path is None or not ckpt_path.exists():
        # Fallback to any existing checkpoint
        for name, path in MODEL_CHECKPOINTS.items():
            if path.exists():
                ckpt_path = path
                break

    if ckpt_path and ckpt_path.exists():
        try:
            logger.info("Loading model checkpoint from: %s", ckpt_path)
            label_map = None
            for search_dir in [ckpt_path.parent, ckpt_path.parent.parent, ckpt_path.parent.parent.parent]:
                lm_file = search_dir / "labels.json"
                if lm_file.exists():
                    with open(lm_file) as f:
                        label_map = json.load(f)
                    break

            cfg = load_model_config("hubert")
            if label_map:
                cfg["num_classes"] = len(label_map)
                cfg["classes"] = label_map
            cfg["layer_pooling"] = "weighted"
            model = load_checkpoint_model(ckpt_path, cfg, DEVICE)
            LOADED_MODELS[model_name] = (model, cfg, label_map)
            return model, cfg, label_map
        except Exception as e:
            logger.error("Failed to load model %s: %s", model_name, e)

    return None, None, None


def process_audio(
    audio_input: Optional[str],
    model_choice: str,
) -> Tuple[Dict[str, float], str, str, str, str, str, str]:
    if audio_input is None:
        empty_probs = {"No Audio": 0.0}
        report = "Please record or upload an audio file to begin analysis."
        return empty_probs, "N/A", "N/A", "N/A", "N/A", "N/A", report

    model, cfg, label_map = get_model(model_choice)

    try:
        metrics = analyze_audio_file(
            audio_path=audio_input,
            model=model,
            cfg=cfg,
            device=DEVICE,
            label_mapping=label_map,
        )
    except Exception as e:
        logger.exception("Analysis error: %s", e)
        return {"Error": 1.0}, "Error", "Error", "Error", "Error", "Error", f"Error during audio processing: {e}"

    # Probabilities for Gradio label component
    probs = metrics.probabilities

    # Formatted display fields
    speed_text = f"{metrics.speaking_speed} ({metrics.syllables_per_second:.1f} syll/sec)"
    pause_text = f"{metrics.pause_frequency} ({metrics.pauses_per_minute:.1f} pauses/min, {metrics.pause_ratio * 100:.1f}% silence)"
    energy_text = f"{metrics.energy} ({metrics.rms_db:.1f} dB)"
    pitch_text = f"{metrics.pitch_variation} (std: {metrics.pitch_std_hz:.1f} Hz)"
    behaviour_text = metrics.overall_behaviour
    full_report = metrics.to_report()

    return (
        probs,
        metrics.emotion.capitalize(),
        speed_text,
        pause_text,
        energy_text,
        pitch_text,
        full_report,
    )


def create_demo() -> gr.Blocks:
    sample_files = [
        ["data/hindi/audio/hindi_00001.wav"],
        ["data/hindi/audio/hindi_00007.wav"],
        ["data/hindi/audio/hindi_00015.wav"],
    ]
    # Filter existing sample files
    available_samples = [s for s in sample_files if (PROJECT_ROOT / s[0]).exists()]

    custom_theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="blue",
        neutral_hue="slate",
    )

    with gr.Blocks(title="Speech Emotion & Audio Behaviour Intelligence") as demo:
        gr.Markdown(
            """
            # Speech Emotion Recognition & Audio Behaviour Intelligence
            ### Multi-Corpus Foundation Models (English & Hindi) | Acoustic Prosody & Speaker Profiling
            """
        )

        with gr.Row():
            with gr.Column(scale=4):
                audio_in = gr.Audio(
                    sources=["microphone", "upload"],
                    type="filepath",
                    label="Audio Input (Speak into mic or upload .wav / .mp3)",
                )

                model_dropdown = gr.Dropdown(
                    choices=list(MODEL_CHECKPOINTS.keys()),
                    value=list(MODEL_CHECKPOINTS.keys())[0],
                    label="Select SER Foundation Architecture",
                )

                analyze_btn = gr.Button("Analyze Speech Behaviour", variant="primary", size="lg")

                if available_samples:
                    gr.Examples(
                        examples=available_samples,
                        inputs=audio_in,
                        label="Example Audio Clips (Hindi Speech Corpus)",
                    )

            with gr.Column(scale=6):
                with gr.Group():
                    gr.Markdown("### 1. Emotion Classification & Probability")
                    label_out = gr.Label(num_top_classes=5, label="Predicted Emotion Distribution")

                with gr.Group():
                    gr.Markdown("### 2. Acoustic Prosody & Diagnostic Meters")
                    with gr.Row():
                        pred_emotion_box = gr.Textbox(label="Top Emotion", interactive=False)
                        energy_box = gr.Textbox(label="Vocal Energy", interactive=False)
                    with gr.Row():
                        speed_box = gr.Textbox(label="Speaking Speed", interactive=False)
                        pause_box = gr.Textbox(label="Pause Frequency", interactive=False)
                    with gr.Row():
                        pitch_box = gr.Textbox(label="Pitch Variation (F0)", interactive=False)

                with gr.Group():
                    gr.Markdown("### 3. Diagnostic Behaviour Analysis Report Card")
                    report_box = gr.Textbox(
                        label="Official Audio Behaviour Analysis Report",
                        lines=12,
                        interactive=False,
                    )

        analyze_btn.click(
            fn=process_audio,
            inputs=[audio_in, model_dropdown],
            outputs=[
                label_out,
                pred_emotion_box,
                speed_box,
                pause_box,
                energy_box,
                pitch_box,
                report_box,
            ],
        )

    return demo


if __name__ == "__main__":
    demo = create_demo()
    custom_theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="blue",
        neutral_hue="slate",
    )
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, theme=custom_theme)
