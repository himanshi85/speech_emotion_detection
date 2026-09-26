# Speech Emotion Recognition — Frontend

Next.js UI for recording or uploading audio, selecting a trained model, and viewing the inference report.

## Prerequisites

1. Trained checkpoint for at least one model under `outputs/<model_key>/checkpoints/best_model/`
2. Python inference API (separate from Next.js)

```bash
# From repo root (with venv activated)
pip install fastapi uvicorn
python scripts/inference_api.py
```

API default: `http://127.0.0.1:8000`

## Run the frontend

```bash
cd frontend
cp .env.example .env.local   # optional — change API URL
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Inference API base URL |

## Features

- **Record** — live mic capture with pause / resume / stop and waveform preview
- **Upload** — drag-and-drop or file picker for common audio formats
- **Model picker** — all 8 SER models; disables entries without a checkpoint
- **Analyze** — calls `POST /predict` and shows predicted emotion, confidence, and per-class bars
