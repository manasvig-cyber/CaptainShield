"""
AegisGuard — Adaptive DoS Simulation & Isolation Forest Defense Lab Launcher
=============================================================================

Starts the AegisGuard modular Python backend (Flask + SQLite + Redis Layer + Isolation Forest)
and the Cyberpunk 3D Web3 Frontend (React + Vite + Three.js).
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

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
BACKEND_MAIN = BACKEND_DIR / "main.py"
FRONTEND_DIR = ROOT_DIR / "frontend"

BACKEND_HEALTH_URL = "http://127.0.0.1:5000/health"
FRONTEND_URL = "http://127.0.0.1:5173/"


def is_service_online(url: str, timeout: float = 1.2) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as res:
            return res.status == 200
    except Exception:
        return False


def main():
    print("=" * 70)
    print("   CAPTAINSHIELD — ADAPTIVE DDOS DEFENSE & RATE LIMITING")
    print("=" * 70)
    print("  [MODE] LAB SIMULATION MODE (Safe Localhost / Private Subnets Only)")
    print("  [CORE] Isolation Forest ML Anomaly Detection + Adaptive Rate Limiter")
    print("  [DATA] Redis Streams Real-Time Telemetry Pipeline & SQLite Persistence")
    print("-" * 70)

    # 1. Start Python Backend
    if is_service_online(BACKEND_HEALTH_URL):
        print("  [OK] CaptainShield Python Gateway is active on http://127.0.0.1:5000")
    else:
        print("  [*] Launching CaptainShield Python Defense Gateway on Port 5000...")
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        subprocess.Popen(
            [sys.executable, str(BACKEND_MAIN)],
            cwd=str(BACKEND_DIR),
            creationflags=creationflags,
        )

        for _ in range(12):
            time.sleep(1.0)
            if is_service_online(BACKEND_HEALTH_URL):
                print("  [OK] Backend started successfully.")
                break
        else:
            print("  [!] Backend taking longer to initialize; continuing...")

    # 2. Start Frontend Dev Server
    if is_service_online(FRONTEND_URL):
        print("  [OK] CaptainShield 3D Web GUI is active on http://127.0.0.1:5173")
    else:
        print("  [*] Launching Vite 3D Web GUI dev server on Port 5173...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        use_shell = os.name == "nt"
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
            cwd=str(FRONTEND_DIR),
            creationflags=creationflags,
            shell=use_shell,
        )

        for _ in range(15):
            time.sleep(1.0)
            if is_service_online(FRONTEND_URL):
                print("  [OK] Frontend dev server started successfully.")
                break
        else:
            print("  [!] Frontend dev server taking longer to initialize; continuing...")

    print("-" * 70)
    print(f"  [+] Command Center Dashboard: {FRONTEND_URL}")
    print("  [+] Wireshark Capture Filter: tcp.port == 5000 and http")
    print("  [+] Interface: Npcap Loopback Adapter (Windows) / lo0")
    print("=" * 70)
    print("  [INFO] CaptainShield Defense Lab is ACTIVE.")
    print("  [INFO] Press Ctrl+C at any time in this window to stop.")
    print("=" * 70)
    webbrowser.open(FRONTEND_URL)

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[!] Shutting down CaptainShield services...")


if __name__ == "__main__":
    main()
