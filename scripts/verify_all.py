#!/usr/bin/env python3
"""Run all XLS-R SER verification steps."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from xlsr.cli import main  # noqa: E402

if __name__ == "__main__":
    extra = ["verify", "all"] + sys.argv[1:]
    raise SystemExit(main(extra))
