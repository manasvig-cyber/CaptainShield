"""
AegisGuard Backend Server Entry Point
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, jsonify, request
from flask_cors import CORS
from app.api import api_bp
from app.database import init_db
from app.config import LAB_TARGET_PORT

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Register REST endpoints
app.register_blueprint(api_bp)

@app.route("/")
def index():
    return jsonify({
        "service": "AegisGuard Defense Lab Gateway",
        "mode": "LAB_SIMULATION_MODE",
        "api_docs": "/api/health",
        "target_endpoint": "/lab/target",
    })

def start_server():
    init_db()
    print("=" * 65)
    print("  🛡️  AEGISGUARD ADAPTIVE DEFENSE & SIMULATION GATEWAY")
    print("=" * 65)
    print(f"  [+] Host: 127.0.0.1  |  Port: {LAB_TARGET_PORT}")
    print("  [+] Mode: LAB SIMULATION ONLY")
    print("  [+] Database: SQLite initialized")
    print("  [+] Wireshark Capture: Select Loopback Adapter (Port 5000)")
    print("=" * 65)
    app.run(host="127.0.0.1", port=LAB_TARGET_PORT, debug=False, threaded=True)

if __name__ == "__main__":
    start_server()
