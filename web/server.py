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

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))

# Model registry definitions
MODELS_CATALOG = {
    "hindi_mfcc_cnn_bilstm": {
        "id": "hindi_mfcc_cnn_bilstm",
        "name": "Hindi Emotion Specialist (MFCC + CNN-BiLSTM)",
        "accuracy": "75.2% Test Accuracy",
        "language": "Hindi / Indic Accents",
        "model_key": "mfcc_cnn_bilstm",
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
        "checkpoint_path": PROJECT_ROOT / "outputs" / "ravdess_enhanced" / "hubert_transfer_cremad_weighted" / "checkpoints" / "best_model" / "model.pt",
        "classes": ["neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprised"],
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
        logger.warning("Checkpoint not found at %s. Searching fallback...", ckpt_path)
        return None, None, None

    try:
        # Resolve config
        config_file = None
        for search_dir in [ckpt_path.parent, ckpt_path.parent.parent, ckpt_path.parent.parent.parent]:
            cf = search_dir / "config.yaml"
            if cf.exists():
                config_file = cf
                break

        cfg = load_model_config(model_key)
        if config_file:
            import yaml
            with open(config_file) as f:
                saved_cfg = yaml.safe_load(f)
            if saved_cfg:
                cfg.update(saved_cfg)

        # Resolve labels
        label_map = None
        data_dir = cfg.get("data_dir")
        if data_dir and (Path(data_dir) / "metadata" / "labels.json").exists():
            with open(Path(data_dir) / "metadata" / "labels.json") as f:
                label_map = json.load(f)
        else:
            for search_dir in [ckpt_path.parent, ckpt_path.parent.parent, ckpt_path.parent.parent.parent]:
                lm_file = search_dir / "labels.json"
                if lm_file.exists():
                    with open(lm_file) as f:
                        label_map = json.load(f)
                    break

        if label_map:
            cfg["num_classes"] = len(label_map)
            cfg["classes"] = label_map
        if model_key == "hubert":
            cfg["layer_pooling"] = "weighted"

        model = build_model(cfg).to(DEVICE)
        ckpt_dir = ckpt_path if ckpt_path.is_dir() else ckpt_path.parent
        load_checkpoint_model(ckpt_dir, model)
        model.eval()

        bundle = (model, cfg, label_map)
        LOADED_MODELS_CACHE[model_id] = bundle
        logger.info("Successfully loaded and cached model: %s", model_id)
        return bundle
    except Exception as e:
        logger.error("Error loading model %s: %s", model_id, e)
        return None, None, None


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
