"""
AegisGuard Configuration & Safety Validation
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "aegisguard.db"
MODEL_PATH = BASE_DIR.parent / "AegisGuard" / "ml_detector_runtime.pkl"

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

LAB_TARGET_HOST = "127.0.0.1"
LAB_TARGET_PORT = 5000
LAB_TARGET_URL = f"http://{LAB_TARGET_HOST}:{LAB_TARGET_PORT}/lab/target"

# Strict safety bounds for defensive laboratory traffic
MAX_ALLOWED_WORKERS = 32
MAX_ALLOWED_DURATION_SECONDS = 86400
MAX_ALLOWED_REQUEST_RATE = 500.0

ALLOWED_TARGET_HOSTS = {
    "127.0.0.1",
    "::1",
    "localhost",
}

def validate_lab_target(target_url: str) -> tuple[bool, str]:
    """Validate that target URL is strictly a localhost or private laboratory target."""
    try:
        parsed = urlparse(target_url)
        hostname = parsed.hostname or ""
        
        if hostname in ALLOWED_TARGET_HOSTS:
            return True, "Valid localhost lab target"
            
        # Allow private RFC1918 IPs in lab setting
        if hostname.startswith("192.168.") or hostname.startswith("10.") or hostname.startswith("172."):
            return True, "Valid private lab target"
            
        return False, f"Target '{hostname}' is not an authorized localhost or private laboratory target."
    except Exception as exc:
        return False, f"Invalid target URL: {exc}"
