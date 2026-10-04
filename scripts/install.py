#!/usr/bin/env python3
"""Register and install this project through the supported Codex CLI."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    subprocess.run(["codex", "plugin", "marketplace", "add", str(ROOT)], check=True)
    subprocess.run(["codex", "plugin", "add", "personal-mem@personal-mem-local"], check=True)
    print("Installed. Start a new Codex conversation; if not listed, restart the desktop app.")
