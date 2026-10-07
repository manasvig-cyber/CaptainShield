"""
AegisGuard Search Engine & Network Forensic Service
Searches live Redis stream, active memory telemetry, and SQLite historical database.
Supports IPv4, IPv6, Client IDs, Session IDs, HTTP status codes, and Incidents.
"""
from __future__ import annotations

import ipaddress
import time
from typing import Any, Dict, List, Optional
from app.database import get_db_connection, get_ip_summary, get_session_by_id
from app.redis_layer import redis_manager

# Known simulated IP mapping for lab workers
DEFAULT_CLIENT_IPS = {
    "SIM-CLIENT-001": "192.168.1.25",
    "SIM-CLIENT-002": "10.0.0.15",
    "SIM-CLIENT-003": "192.168.1.101",
    "SIM-CLIENT-004": "172.16.0.50",
    "SIM-CLIENT-005": "192.168.1.88",
    "SIM-CLIENT-006": "10.0.1.42",
    "SIM-CLIENT-007": "192.168.2.14",
    "SIM-CLIENT-008": "127.0.0.1",
}


def validate_ip(ip_str: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Validate if string is a valid IPv4 or IPv6 address using ipaddress module."""
    try:
        obj = ipaddress.ip_address(ip_str.strip())
        return True, f"IPv{obj.version}", str(obj)
    except ValueError:
        return False, None, None


def search_all(query: str, active_sim=None) -> Dict[str, Any]:
    """
    Unified search handler for top search bar.
    Searches active simulation live telemetry and SQLite database.
    """
    q = query.strip()
    if not q:
        return {"found": False, "query": q, "message": "Search query is empty."}

    # 1. Check if IP address (IPv4 or IPv6)
    is_ip, ip_version, canonical_ip = validate_ip(q)
    if is_ip and canonical_ip:
        return search_ip(canonical_ip, ip_version, active_sim)

    # 2. Check if HTTP status code (200, 429, 500, 503, etc.)
    if q.isdigit() and len(q) == 3:
        return search_status_code(int(q), active_sim)

    # 3. Check if Session ID (starts with SIM- or matches simulation_sessions)
    if q.upper().startswith("SIM-") or len(q) >= 6:
        sess = get_session_by_id(q.upper())
        if sess:
            return {
                "found": True,
                "matched_type": "SESSION",
                "session_id": sess["id"],
                "preset": sess["preset"],
                "status": sess["status"],
                "total_requests": sess["total_requests"],
                "blocked_requests": sess["blocked_requests"],
                "peak_rate": sess["peak_rate"],
                "avg_latency_ms": sess["avg_latency"],
                "avg_risk_score": sess["avg_risk_score"],
                "created_at": sess["created_at"],
            }

    # 4. Check if Incident ID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE incident_id LIKE ? LIMIT 5", (f"%{q}%",))
    inc_rows = cursor.fetchall()
    if inc_rows:
        conn.close()
        inc = dict(inc_rows[0])
        return {
            "found": True,
            "matched_type": "INCIDENT",
            "incident_id": inc["incident_id"],
            "session_id": inc["session_id"],
            "severity": inc["severity"],
            "status": inc["status"],
            "description": inc["description"],
            "trigger": inc["trigger"],
            "actions_taken": inc["actions_taken"],
            "blocked_requests": inc["blocked_requests"],
            "opened_at": inc["opened_at"],
        }

    # 5. Search by Client ID (e.g. SIM-CLIENT-001) or general keyword
    cursor.execute("""
    SELECT DISTINCT client_ip, client_id, session_id, COUNT(*) as cnt 
    FROM request_logs 
    WHERE client_id LIKE ? OR target_url LIKE ?
    GROUP BY client_ip, client_id
    LIMIT 10
    """, (f"%{q}%", f"%{q}%"))
    matches = cursor.fetchall()
    conn.close()

    if matches:
        first = dict(matches[0])
        return {
            "found": True,
            "matched_type": "CLIENT",
            "client_id": first.get("client_id"),
            "associated_ip": first.get("client_ip"),
            "total_logged": sum(m["cnt"] for m in matches),
            "matches": [dict(m) for m in matches],
        }

    # Check active simulation memory for matches
    if active_sim and active_sim.is_running:
        if q in DEFAULT_CLIENT_IPS.values() or q in DEFAULT_CLIENT_IPS:
            return search_ip(q, "IPv4", active_sim)

    return {
        "found": False,
        "query": q,
        "message": f"No network activity or forensic records found matching '{q}'.",
    }


def search_ip(ip_str: str, version: str, active_sim=None) -> Dict[str, Any]:
    """Deep forensic inspection for an IP address across live stream and SQLite history."""
    # 1. Query persistent history from SQLite
    summary = get_ip_summary(ip_str)

    # 2. Check if active in the live simulation right now
    is_live = False
    live_requests = 0
    live_blocked = 0
    current_risk = 0.0

    if active_sim and active_sim.is_running:
        # Check if mapped to any of the active workers
        for client_id, mapped_ip in DEFAULT_CLIENT_IPS.items():
            if mapped_ip == ip_str:
                is_live = True
                # Estimate proportional worker contribution
                num_workers = max(1, active_sim.config.workers)
                live_requests = active_sim.requests_sent // num_workers
                live_blocked = active_sim.blocked_requests // num_workers
                if active_sim.risk_scores:
                    current_risk = active_sim.risk_scores[-1]
                break

    if not summary and not is_live:
        return {
            "found": False,
            "query": ip_str,
            "is_valid_ip": True,
            "ip_version": version,
            "message": f"IP address {ip_str} is valid ({version}), but no network traffic from this address has been observed.",
        }

    # Combine historical and live metrics
    total_reqs = (summary["total_requests"] if summary else 0) + live_requests
    blocked_reqs = (summary["blocked_requests"] if summary else 0) + live_blocked
    successful_reqs = (summary["successful_requests"] if summary else 0) + max(0, live_requests - live_blocked)
    failed_reqs = summary["failed_requests"] if summary else 0
    avg_latency = summary["avg_latency_ms"] if summary else 1.8
    peak_risk = max((summary["peak_risk_score"] if summary else 0.0), current_risk)

    # Determine security assessment status
    if peak_risk >= 60.0 or blocked_reqs > 0:
        status_label = "HIGH RISK"
        status_color = "#ef4444"
    elif peak_risk >= 30.0:
        status_label = "SUSPICIOUS"
        status_color = "#ffd83d"
    else:
        status_label = "BENIGN"
        status_color = "#22d3a2"

    return {
        "found": True,
        "matched_type": "IP_ADDRESS",
        "ip": ip_str,
        "ip_version": version,
        "security_status": status_label,
        "status_color": status_color,
        "risk_score": round(peak_risk, 1),
        "is_currently_active": is_live,
        "total_requests": total_reqs,
        "successful_requests": successful_reqs,
        "blocked_requests": blocked_reqs,
        "failed_requests": failed_reqs,
        "avg_latency_ms": avg_latency,
        "first_seen": summary["first_seen"] if summary else time.time(),
        "last_seen": time.time() if is_live else (summary["last_seen"] if summary else time.time()),
        "sessions": summary["sessions"] if summary else ([active_sim.session_id] if active_sim else []),
        "recent_requests": summary["recent_requests"] if summary else [],
    }


def search_status_code(code: int, active_sim=None) -> Dict[str, Any]:
    """Search for activity by HTTP status code."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT COUNT(*) as cnt, COUNT(DISTINCT client_ip) as unique_ips, AVG(latency_ms) as avg_lat
    FROM request_logs 
    WHERE status_code = ?
    """, (code,))
    row = cursor.fetchone()
    conn.close()

    total_logged = row["cnt"] if row else 0
    unique_ips = row["unique_ips"] if row else 0

    meaning_map = {
        200: "OK - Request successfully processed and served by defense gateway.",
        429: "Too Many Requests - Blocked by Adaptive Rate Limiter / Defense Policy.",
        500: "Internal Server Error - Target service failure.",
        503: "Service Unavailable - Overloaded target simulation server.",
    }

    return {
        "found": total_logged > 0 or (active_sim and active_sim.is_running),
        "matched_type": "STATUS_CODE",
        "status_code": code,
        "meaning": meaning_map.get(code, f"HTTP Status {code}"),
        "total_occurrences": total_logged,
        "unique_source_ips": unique_ips,
        "avg_latency_ms": round(row["avg_lat"] or 0.0, 2) if row else 0.0,
    }


def get_search_suggestions() -> List[Dict[str, str]]:
    """Returns quick suggestions for the search bar dropdown."""
    return [
        {"query": "192.168.1.25", "type": "IP Address (Worker 1)", "desc": "Check simulated client IP telemetry"},
        {"query": "10.0.0.15", "type": "IP Address (Worker 2)", "desc": "Inspect burst request behavior"},
        {"query": "127.0.0.1", "type": "Localhost IP", "desc": "Loopback laboratory target traffic"},
        {"query": "429", "type": "HTTP Status", "desc": "Inspect throttled / rate-limited requests"},
        {"query": "200", "type": "HTTP Status", "desc": "Inspect successfully defended requests"},
        {"query": "SIM-CLIENT-001", "type": "Client ID", "desc": "Forensic trace for worker client 1"},
    ]
