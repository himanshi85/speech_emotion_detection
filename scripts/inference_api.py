#!/usr/bin/env python3
"""
Speech Emotion Recognition — Inference API Server
=================================================
Runs FastAPI backend serving:
1. /health, /models, /predict for the Next.js Studio (port 3000)
2. /api/models, /api/analyze for the Glassmorphic AURA Web GUI (port 8000)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from web.server import app, start_server


def main():
    parser = argparse.ArgumentParser(description="Speech Emotion Recognition Inference API Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    args = parser.parse_args()

    start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
