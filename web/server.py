#!/usr/bin/env python3
"""
FastAPI Backend for Speech Emotion Recognition & Audio Behaviour Intelligence GUI
================================================================================
Serves REST API endpoints for model inference and streams the modern web frontend.
"""

from __future__ import annotations

import io
import json
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import soundfile as sf
import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ser.core.config import load_model_config
from ser.core.registry import build_model
from ser.features.behavior import analyze_audio_file
from ser.training.trainer import load_checkpoint_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("gui_server")

import time

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))

# Model registry definitions
MODELS_CATALOG = {
    "hindi_mfcc_cnn_bilstm": {
        "id": "hindi_mfcc_cnn_bilstm",
        "name": "Hindi Emotion Specialist (MFCC + CNN-BiLSTM)",
        "accuracy": "75.2% Test Accuracy",
        "language": "Hindi / Indic Accents",
        "model_key": "mfcc_cnn_bilstm",
        "input_type": "mfcc",
        "architecture": "MFCC(40) -> CNN(64) -> BiLSTM(128x2) -> Dense(5) [75.2% Acc]",
        "checkpoint_path": PROJECT_ROOT / "outputs" / "hindi" / "mfcc_cnn_bilstm" / "checkpoints" / "best_model" / "model.pt",
        "classes": ["neutral", "calm", "happy", "sad", "angry"],
        "recommended": True,
    },
    "universal_hubert": {
        "id": "universal_hubert",
        "name": "Universal HuBERT Foundation Model (Multi-Corpus)",
        "accuracy": "68.3% Multi-Corpus",
        "language": "English (Universal)",
        "model_key": "hubert",
        "input_type": "waveform",
        "architecture": "HuBERT-Base (960h) -> Weighted Layer Pooling -> Dense(6) [68.3% Multi-Corpus]",
        "checkpoint_path": PROJECT_ROOT / "outputs" / "combined" / "universal_hubert_weighted_frozen" / "checkpoints" / "best_model" / "model.pt",
        "classes": ["neutral", "happy", "sad", "angry", "fear", "disgust"],
        "recommended": False,
    },
    "cremad_hubert": {
        "id": "cremad_hubert",
        "name": "CREMA-D HuBERT (7,442 clips Champion)",
        "accuracy": "75.6% Test Accuracy",
        "language": "English (Diverse Actors)",
        "model_key": "hubert",
        "input_type": "waveform",
        "architecture": "HuBERT-Base -> Mean Pooling -> Dense(6) [75.6% Acc]",
        "checkpoint_path": PROJECT_ROOT / "outputs" / "cremad" / "hubert" / "checkpoints" / "best_model" / "model.pt",
        "classes": ["neutral", "happy", "sad", "angry", "fear", "disgust"],
        "recommended": False,
    },
    "ravdess_hubert": {
        "id": "ravdess_hubert",
        "name": "RAVDESS Transfer HuBERT (Weighted Pooling)",
        "accuracy": "73.8% Test Accuracy",
        "language": "English (Studio Acting)",
        "model_key": "hubert",
        "input_type": "waveform",
        "architecture": "HuBERT-Base (Transfer CREMA-D) -> Weighted Pooling -> Dense(8) [73.8% Acc]",
        "checkpoint_path": PROJECT_ROOT / "outputs" / "ravdess_enhanced" / "hubert_transfer_cremad_weighted" / "checkpoints" / "best_model" / "model.pt",
        "classes": ["neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprised"],
        "recommended": False,
    },
    "mfcc_lstm": {
        "id": "mfcc_lstm",
        "name": "Hindi MFCC + LSTM Baseline",
        "accuracy": "63.6% Test Accuracy",
        "language": "Hindi / Indic Accents",
        "model_key": "mfcc_lstm",
        "input_type": "mfcc",
        "architecture": "MFCC(40) -> LSTM(128x2) -> Dense(5) [63.6% Acc]",
        "checkpoint_path": PROJECT_ROOT / "outputs" / "hindi" / "mfcc_lstm" / "checkpoints" / "best_model" / "model.pt",
        "classes": ["neutral", "calm", "happy", "sad", "angry"],
        "recommended": False,
    },
    "wav2vec2_xlsr_300m": {
        "id": "wav2vec2_xlsr_300m",
        "name": "Wav2Vec2-XLS-R-300M (Multilingual)",
        "accuracy": "62.4% Test Accuracy",
        "language": "Multilingual (128 Languages)",
        "model_key": "wav2vec2_xlsr_300m",
        "input_type": "waveform",
        "architecture": "Wav2Vec2-XLS-R-300M -> Masked Mean Pool -> Dense(7)",
        "checkpoint_path": PROJECT_ROOT / "outputs" / "savee" / "wav2vec2_xlsr_300m" / "checkpoints" / "best_model" / "model.pt",
        "classes": ["neutral", "happy", "sad", "angry", "fear", "disgust", "surprised"],
        "recommended": False,
    },
}

# In-memory model cache
LOADED_MODELS_CACHE: Dict[str, Any] = {}


def get_or_load_model(model_id: str):
    if model_id in LOADED_MODELS_CACHE:
        return LOADED_MODELS_CACHE[model_id]

    meta = MODELS_CATALOG.get(model_id)
    if not meta:
        meta = MODELS_CATALOG["hindi_mfcc_cnn_bilstm"]

    ckpt_path = meta["checkpoint_path"]
    model_key = meta["model_key"]

    if not ckpt_path.exists():
        logger.error("Checkpoint not found at %s.", ckpt_path)
        raise FileNotFoundError(f"Checkpoint not found at {ckpt_path}")

    try:
        ckpt = torch.load(ckpt_path, map_location="cpu")
        state_dict = ckpt.get("model_state_dict", ckpt)
        saved_cfg = ckpt.get("config", {})
        label_map = ckpt.get("label_mapping")

        # Base default config for model key
        cfg = load_model_config(model_key)
        if saved_cfg:
            cfg.update(saved_cfg)

        # Infer classes and num_classes directly from checkpoint
        if not label_map and meta.get("classes"):
            label_map = {c: i for i, c in enumerate(meta["classes"])}

        if label_map:
            cfg["num_classes"] = len(label_map)
            cfg["classes"] = label_map
        else:
            head_weight = state_dict.get("classifier.weight", state_dict.get("fc.weight"))
            if head_weight is not None:
                cfg["num_classes"] = head_weight.shape[0]

        # Infer pooling mechanism directly from state_dict keys
        if any("weighted_pooler" in k for k in state_dict.keys()):
            cfg["layer_pooling"] = "weighted"
        elif "layer_pooling" not in cfg or cfg["layer_pooling"] == "weighted":
            cfg["layer_pooling"] = "mean"

        model = build_model(cfg).to(DEVICE)
        model.load_state_dict(state_dict)
        model.eval()

        bundle = (model, cfg, label_map)
        LOADED_MODELS_CACHE[model_id] = bundle
        logger.info(
            "Successfully loaded and cached model %s (num_classes=%d, pooling=%s)",
            model_id,
            cfg["num_classes"],
            cfg.get("layer_pooling", "none"),
        )
        return bundle
    except Exception as e:
        logger.exception("Error loading model %s from %s: %s", model_id, ckpt_path, e)
        raise RuntimeError(f"Failed to load model {model_id}: {e}")


# FastAPI App Initialization
app = FastAPI(
    title="Speech Emotion Recognition & Audio Behaviour Intelligence",
    description="Interactive Web API for voice diagnostics and emotional classification",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint for Next.js frontend."""
    return {"status": "ok", "device": str(DEVICE)}


@app.get("/models")
def list_models_for_nextjs():
    """Returns model list in format expected by Next.js SerStudio frontend."""
    result = []
    for k, v in MODELS_CATALOG.items():
        result.append({
            "key": v["id"],
            "display_name": v["name"],
            "input_type": v.get("input_type", "waveform"),
            "architecture": v.get("architecture", v["name"]),
            "checkpoint_available": v["checkpoint_path"].exists(),
        })
    return result


@app.post("/predict")
async def predict_endpoint(
    model_key: str = Form(...),
    file: UploadFile = File(...),
):
    """Inference endpoint conforming to Next.js SerStudio AnalysisReport contract."""
    start_time = time.time()
    logger.info("Received /predict request: model_key=%s, filename=%s", model_key, file.filename)

    meta = MODELS_CATALOG.get(model_key)
    if not meta:
        for k, v in MODELS_CATALOG.items():
            if k == model_key or v.get("model_key") == model_key:
                meta = v
                model_key = k
                break
    if not meta:
        meta = MODELS_CATALOG["hindi_mfcc_cnn_bilstm"]
        model_key = "hindi_mfcc_cnn_bilstm"

    suffix = Path(file.filename or "recording.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        shutil.copyfileobj(file.file, tmp)

    try:
        file_size = tmp_path.stat().st_size
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded audio recording is empty (0 bytes).")

        model, cfg, label_map = get_or_load_model(model_key)
        metrics = analyze_audio_file(
            audio_path=tmp_path,
            model=model,
            cfg=cfg,
            device=DEVICE,
            label_mapping=label_map,
        )
        inference_time = time.time() - start_time

        prob_list = []
        label_to_id = {k: v for k, v in (label_map or {}).items()}
        for i, (emo_name, prob_val) in enumerate(metrics.probabilities.items()):
            lid = label_to_id.get(emo_name, i)
            prob_list.append({
                "emotion": emo_name,
                "label_id": lid,
                "probability": round(float(prob_val), 4),
            })
        prob_list.sort(key=lambda x: x["probability"], reverse=True)

        pred_label_id = label_to_id.get(metrics.emotion, 0)
        summary_str = (
            f"Predicted emotion: {metrics.emotion.capitalize()} ({metrics.confidence * 100.0:.1f}% confidence). "
            f"Acoustic behavioural profile: {metrics.overall_behaviour}. "
            f"Speech tempo: {metrics.speaking_speed} ({metrics.syllables_per_second:.1f} syll/sec, {int(round(metrics.words_per_minute))} WPM). "
            f"Pauses: {metrics.pause_frequency} ({metrics.pauses_per_minute:.1f}/min, {metrics.pause_ratio * 100.0:.1f}% silence). "
            f"Energy: {metrics.energy} ({metrics.rms_db:.1f} dB RMS). "
            f"Pitch: {metrics.pitch_variation} ({metrics.pitch_mean_hz:.1f} Hz mean, {metrics.pitch_std_hz:.1f} Hz std)."
        )

        return JSONResponse(content={
            "model_key": model_key,
            "display_name": meta["name"],
            "predicted_emotion": metrics.emotion,
            "predicted_label_id": pred_label_id,
            "confidence": round(float(metrics.confidence), 4),
            "probabilities": prob_list,
            "inference_time_sec": round(inference_time, 3),
            "audio_duration_sec": round(metrics.audio_duration_seconds, 2),
            "sample_rate": 16000,
            "summary": summary_str,
        })
    except Exception as e:
        logger.exception("Error in /predict endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)


@app.get("/api/models")
def list_models():
    """Returns available models with metadata."""
    models_list = []
    for k, v in MODELS_CATALOG.items():
        models_list.append({
            "id": v["id"],
            "name": v["name"],
            "accuracy": v["accuracy"],
            "language": v["language"],
            "classes": v["classes"],
            "recommended": v["recommended"],
            "available": v["checkpoint_path"].exists(),
        })
    return {"models": models_list, "device": str(DEVICE)}


@app.get("/api/samples")
def list_sample_clips():
    """Returns list of pre-configured sample audio clips for instant testing."""
    samples = [
        {
            "id": "hindi_1",
            "name": "Hindi Sample 1 (Neutral / Conversational)",
            "path": "data/hindi/audio/hindi_00001.wav",
            "language": "Hindi",
            "expected_emotion": "Neutral",
        },
        {
            "id": "hindi_7",
            "name": "Hindi Sample 2 (Happy / Expressive)",
            "path": "data/hindi/audio/hindi_00007.wav",
            "language": "Hindi",
            "expected_emotion": "Happy",
        },
        {
            "id": "hindi_15",
            "name": "Hindi Sample 3 (Angry / Assertive)",
            "path": "data/hindi/audio/hindi_00015.wav",
            "language": "Hindi",
            "expected_emotion": "Angry",
        },
    ]

    valid_samples = []
    for s in samples:
        full_path = PROJECT_ROOT / s["path"]
        if full_path.exists():
            valid_samples.append({
                "id": s["id"],
                "name": s["name"],
                "language": s["language"],
                "expected": s["expected_emotion"],
                "url": f"/api/sample-audio/{s['id']}",
            })
    return {"samples": valid_samples}


@app.get("/api/sample-audio/{sample_id}")
def get_sample_audio(sample_id: str):
    """Streams a sample audio file."""
    id_map = {
        "hindi_1": PROJECT_ROOT / "data/hindi/audio/hindi_00001.wav",
        "hindi_7": PROJECT_ROOT / "data/hindi/audio/hindi_00007.wav",
        "hindi_15": PROJECT_ROOT / "data/hindi/audio/hindi_00015.wav",
    }
    file_path = id_map.get(sample_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample audio not found")
    return FileResponse(path=file_path, media_type="audio/wav")


@app.post("/api/analyze")
async def analyze_audio_endpoint(
    file: UploadFile = File(...),
    model_id: str = Form("hindi_mfcc_cnn_bilstm"),
):
    """Processes uploaded audio (or microphone recording) and returns full behavior report."""
    logger.info("Received analyze request: filename=%s, model_id=%s", file.filename, model_id)

    # Save uploaded file to temp file
    suffix = Path(file.filename or "recording.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        shutil.copyfileobj(file.file, tmp)

    file_size = tmp_path.stat().st_size
    logger.info("Saved temp file %s (%d bytes)", tmp_path, file_size)
    if file_size == 0:
        if tmp_path.exists():
            os.remove(tmp_path)
        raise HTTPException(status_code=400, detail="Uploaded audio recording is empty (0 bytes). Please record or select a valid audio clip.")

    try:
        # Load requested model
        model, cfg, label_map = get_or_load_model(model_id)

        # Analyze audio file
        metrics = analyze_audio_file(
            audio_path=tmp_path,
            model=model,
            cfg=cfg,
            device=DEVICE,
            label_mapping=label_map,
        )

        response_payload = {
            "success": True,
            "filename": file.filename,
            "duration": round(metrics.audio_duration_seconds, 2),
            "emotion": metrics.emotion,
            "confidence": round(metrics.confidence * 100.0, 1),
            "probabilities": {k: round(v * 100.0, 1) for k, v in metrics.probabilities.items()},
            "speaking_speed": {
                "category": metrics.speaking_speed,
                "syllables_per_second": round(metrics.syllables_per_second, 1),
                "words_per_minute": int(round(metrics.words_per_minute)),
            },
            "pause_frequency": {
                "category": metrics.pause_frequency,
                "pauses_per_minute": round(metrics.pauses_per_minute, 1),
                "silence_ratio": round(metrics.pause_ratio * 100.0, 1),
            },
            "vocal_energy": {
                "category": metrics.energy,
                "rms_db": round(metrics.rms_db, 1),
            },
            "pitch_variation": {
                "category": metrics.pitch_variation,
                "mean_hz": round(metrics.pitch_mean_hz, 1),
                "std_hz": round(metrics.pitch_std_hz, 1),
            },
            "overall_behaviour": metrics.overall_behaviour,
            "report_text": metrics.to_report(),
        }
        return JSONResponse(content=response_payload)
    except Exception as e:
        logger.exception("Error in analyze_audio_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)


# Mount static web frontend
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def start_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    print(f"\n=======================================================")
    print(f"  Speech Emotion & Audio Behaviour Intelligence GUI")
    print(f"  URL: http://{host}:{port}")
    print(f"=======================================================\n")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
