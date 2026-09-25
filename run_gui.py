#!/usr/bin/env python3
"""
Launcher for AURA | Speech Emotion Recognition & Audio Behaviour Intelligence Web GUI
====================================================================================
Runs the FastAPI web server on http://127.0.0.1:8000.
"""

from __future__ import annotations

import argparse
import socket
import sys
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import uvicorn


def find_free_port(start_port: int = 8000) -> int:
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


def main():
    parser = argparse.ArgumentParser(description="Start AURA Web GUI Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="Port (default: 8000 or first available)")
    parser.add_argument("--open-browser", action="store_true", help="Automatically open browser")
    args = parser.parse_args()

    port = args.port or find_free_port(8000)
    url = f"http://{args.host}:{port}"

    print("\n" + "=" * 65)
    print("   AURA | Speech Emotion & Audio Behaviour Intelligence GUI")
    print("=" * 65)
    print(f"  URL:           {url}")
    print(f"  Host:          {args.host}")
    print(f"  Port:          {port}")
    print(f"  Hindi Model:   outputs/hindi/mfcc_cnn_bilstm (74.4% - 75.2%)")
    print(f"  Foundation:    outputs/combined/universal_hubert (68.3%)")
    print("=" * 65)
    print("  Press Ctrl+C to stop the web server.\n")

    if args.open_browser:
        webbrowser.open(url)

    from web.server import app
    uvicorn.run(app, host=args.host, port=port, log_level="info")


if __name__ == "__main__":
    main()
