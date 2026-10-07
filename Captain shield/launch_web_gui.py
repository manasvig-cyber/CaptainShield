"""
AegisGuard — 3D Cyber-Tech Dashboard Launcher
=============================================

Starts the AegisGuard Flask backend (if not running) and launches
the modern Three.js / React 3D Web3 Cyberpunk Dashboard in your browser.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
APP_FILE = CURRENT_DIR / "app.py"

BACKEND_URL = "http://127.0.0.1:5000/health"
FRONTEND_URL = "http://127.0.0.1:5173/"


def is_backend_running() -> bool:
    try:
        with urllib.request.urlopen(BACKEND_URL, timeout=1.5) as res:
            return res.status == 200
    except Exception:
        return False


def is_frontend_running() -> bool:
    try:
        with urllib.request.urlopen(FRONTEND_URL, timeout=1.5) as res:
            return res.status == 200
    except Exception:
        return False


def main():
    print("=" * 65)
    print("  [AEGISGUARD] 3D ADAPTIVE DEFENSE CORE LAUNCHER")
    print("=" * 65)

    # 1. Start Flask backend if not running
    if is_backend_running():
        print("  [OK] AegisGuard Flask Gateway is already running (Port 5000)")
    else:
        print("  [*] Launching AegisGuard Flask Gateway on Port 5000...")
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        subprocess.Popen(
            [sys.executable, str(APP_FILE)],
            cwd=str(CURRENT_DIR),
            creationflags=creationflags,
        )
        time.sleep(1.5)

    # 2. Check frontend dev server
    if is_frontend_running():
        print(f"  [OK] 3D Dashboard is active at: {FRONTEND_URL}")
    else:
        print("  [*] Launching Vite 3D Dashboard dev server...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
            cwd=str(FRONTEND_DIR),
            creationflags=creationflags,
        )
        time.sleep(2.0)

    print()
    print(f"  [+] Opening 3D Cyberpunk Dashboard in browser: {FRONTEND_URL}")
    print("=" * 65)
    webbrowser.open(FRONTEND_URL)


if __name__ == "__main__":
    main()
