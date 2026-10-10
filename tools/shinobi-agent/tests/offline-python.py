#!/usr/bin/env python3
"""Test launcher for a real runner with only model generation patched offline."""
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.execv(str(root / ".venv/bin/python"), [str(root / ".venv/bin/python"), str(root / "tests/offline_runner.py")])
