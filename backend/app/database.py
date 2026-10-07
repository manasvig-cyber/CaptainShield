"""
AegisGuard SQLite Database Layer for Persistent History & Reports
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.config import DB_PATH


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS simulation_sessions (
        id TEXT PRIMARY KEY,
        preset TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL,
        duration REAL,
        total_requests INTEGER DEFAULT 0,
        successful_requests INTEGER DEFAULT 0,
        blocked_requests INTEGER DEFAULT 0,
        failed_requests INTEGER DEFAULT 0,
        peak_rate REAL DEFAULT 0.0,
        avg_latency REAL DEFAULT 0.0,
        avg_risk_score REAL DEFAULT 0.0,
        max_risk_score REAL DEFAULT 0.0,
        defense_capacity REAL DEFAULT 100.0,
        incident_count INTEGER DEFAULT 0,
        status TEXT NOT NULL,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS simulation_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp REAL NOT NULL,
        request_rate REAL,
        burstiness REAL,
        latency REAL,
        error_rate REAL,
        active_clients INTEGER,
        risk_score REAL,
        defense_level TEXT,
        capacity REAL,
        FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS telemetry_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp REAL NOT NULL,
        client_id TEXT NOT NULL,
        request_rate REAL,
        request_interval REAL,
        burstiness REAL,
        latency REAL,
        client_frequency REAL,
        request_size REAL,
        error_rate REAL,
        status_code INTEGER,
        FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS incidents (
        incident_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        severity TEXT NOT NULL,
        description TEXT,
        opened_at REAL NOT NULL,
        detected_at REAL,
        defense_started_at REAL,
        recovered_at REAL,
        status TEXT NOT NULL,
        peak_risk REAL,
        trigger TEXT,
        actions_taken TEXT,
        affected_requests INTEGER DEFAULT 0,
        blocked_requests INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS defense_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp REAL NOT NULL,
        client_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        risk_score REAL,
        limit_assigned INTEGER,
        duration_sec REAL,
        reason TEXT,
        FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS request_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp REAL NOT NULL,
        client_id TEXT NOT NULL,
        client_ip TEXT NOT NULL,
        target_url TEXT NOT NULL,
        method TEXT DEFAULT 'GET',
        status_code INTEGER,
        latency_ms REAL,
        size_bytes INTEGER,
        risk_score REAL DEFAULT 0.0,
        blocked BOOLEAN DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_req_ip ON request_logs(client_ip);
    CREATE INDEX IF NOT EXISTS idx_req_session ON request_logs(session_id);
    CREATE INDEX IF NOT EXISTS idx_req_status ON request_logs(status_code);

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed default settings if empty
    default_settings = {
        "app_name": "CaptainShield Defense Lab",
        "lab_mode": "true",
        "default_preset": "Controlled Attack",
        "default_workers": "6",
        "default_rate": "50",
        "default_duration": "30",
        "max_duration": "300",
        "target_url": "http://127.0.0.1:5000/lab/target",
        "anomaly_sensitivity": "0.05",
        "risk_threshold_watch": "30",
        "risk_threshold_suspicious": "60",
        "risk_threshold_high": "80",
        "rate_limiting_enabled": "true",
        "wireshark_interface": "Npcap Loopback Adapter",
    }

    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()


def save_session(session_data: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO simulation_sessions (
        id, preset, start_time, end_time, duration,
        total_requests, successful_requests, blocked_requests, failed_requests,
        peak_rate, avg_latency, avg_risk_score, max_risk_score,
        defense_capacity, incident_count, status, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_data.get("id"),
        session_data.get("preset", "Custom"),
        session_data.get("start_time", 0.0),
        session_data.get("end_time", 0.0),
        session_data.get("duration", 0.0),
        session_data.get("total_requests", 0),
        session_data.get("successful_requests", 0),
        session_data.get("blocked_requests", 0),
        session_data.get("failed_requests", 0),
        session_data.get("peak_rate", 0.0),
        session_data.get("avg_latency", 0.0),
        session_data.get("avg_risk_score", 0.0),
        session_data.get("max_risk_score", 0.0),
        session_data.get("defense_capacity", 100.0),
        session_data.get("incident_count", 0),
        session_data.get("status", "COMPLETED"),
        session_data.get("notes", "")
    ))
    conn.commit()
    conn.close()


def get_all_sessions() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM simulation_sessions ORDER BY start_time DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM simulation_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(session_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM simulation_sessions WHERE id = ?", (session_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def save_incident(incident_data: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO incidents (
        incident_id, session_id, severity, description,
        opened_at, detected_at, defense_started_at, recovered_at,
        status, peak_risk, trigger, actions_taken, affected_requests, blocked_requests
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident_data.get("incident_id"),
        incident_data.get("session_id"),
        incident_data.get("severity", "LOW"),
        incident_data.get("description", ""),
        incident_data.get("opened_at", 0.0),
        incident_data.get("detected_at"),
        incident_data.get("defense_started_at"),
        incident_data.get("recovered_at"),
        incident_data.get("status", "RECOVERED"),
        incident_data.get("peak_risk", 0.0),
        incident_data.get("trigger", ""),
        incident_data.get("actions_taken", ""),
        incident_data.get("affected_requests", 0),
        incident_data.get("blocked_requests", 0)
    ))
    conn.commit()
    conn.close()


def get_incidents_for_session(session_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE session_id = ? ORDER BY opened_at ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_settings() -> Dict[str, str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


def update_settings(new_settings: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    for k, v in new_settings.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (k, str(v)))
    conn.commit()
    conn.close()


def log_request(
    session_id: str,
    client_id: str,
    client_ip: str,
    target_url: str,
    method: str = "GET",
    status_code: int = 200,
    latency_ms: float = 0.0,
    size_bytes: int = 128,
    risk_score: float = 0.0,
    blocked: bool = False,
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO request_logs (
            session_id, timestamp, client_id, client_ip, target_url,
            method, status_code, latency_ms, size_bytes, risk_score, blocked
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            time.time() if "time" in globals() else datetime.utcnow().timestamp(),
            client_id,
            client_ip,
            target_url,
            method,
            status_code,
            latency_ms,
            size_bytes,
            risk_score,
            1 if blocked else 0,
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_ip_summary(client_ip: str) -> Optional[Dict[str, Any]]:
    """Returns aggregated stats for an IP address across all sessions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        COUNT(*) as total_requests,
        SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as successful_requests,
        SUM(CASE WHEN status_code = 429 THEN 1 ELSE 0 END) as blocked_requests,
        SUM(CASE WHEN status_code NOT IN (200, 429) THEN 1 ELSE 0 END) as failed_requests,
        AVG(latency_ms) as avg_latency,
        MAX(risk_score) as peak_risk,
        AVG(risk_score) as avg_risk,
        MIN(timestamp) as first_seen,
        MAX(timestamp) as last_seen
    FROM request_logs 
    WHERE client_ip = ?
    """, (client_ip,))
    row = cursor.fetchone()

    if not row or row["total_requests"] == 0:
        conn.close()
        return None

    # Get associated sessions
    cursor.execute("SELECT DISTINCT session_id FROM request_logs WHERE client_ip = ?", (client_ip,))
    sessions = [r["session_id"] for r in cursor.fetchall()]

    # Get recent 15 requests
    cursor.execute("""
    SELECT timestamp, session_id, client_id, target_url, method, status_code, latency_ms, risk_score, blocked
    FROM request_logs
    WHERE client_ip = ?
    ORDER BY timestamp DESC
    LIMIT 15
    """, (client_ip,))
    recent = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "ip": client_ip,
        "total_requests": row["total_requests"],
        "successful_requests": row["successful_requests"] or 0,
        "blocked_requests": row["blocked_requests"] or 0,
        "failed_requests": row["failed_requests"] or 0,
        "avg_latency_ms": round(row["avg_latency"] or 0.0, 2),
        "peak_risk_score": round(row["peak_risk"] or 0.0, 1),
        "avg_risk_score": round(row["avg_risk"] or 0.0, 1),
        "first_seen": row["first_seen"],
        "last_seen": row["last_seen"],
        "sessions": sessions,
        "recent_requests": recent,
    }
