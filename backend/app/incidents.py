"""
AegisGuard Incident Lifecycle Engine
Tracks incident state: CREATED -> INVESTIGATING -> DEFENSE_ACTIVE -> MITIGATING -> RECOVERED / ESCALATED.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from threading import Lock
from typing import Dict, List, Optional
from app.database import save_incident


@dataclass
class IncidentState:
    incident_id: str
    session_id: str
    severity: str
    description: str
    opened_at: float
    detected_at: float
    defense_started_at: Optional[float]
    recovered_at: Optional[float]
    status: str
    peak_risk: float
    trigger: str
    actions_taken: List[str]
    affected_requests: int
    blocked_requests: int

    def to_dict(self) -> Dict:
        return {
            "incident_id": self.incident_id,
            "session_id": self.session_id,
            "severity": self.severity,
            "description": self.description,
            "opened_at": self.opened_at,
            "detected_at": self.detected_at,
            "defense_started_at": self.defense_started_at,
            "recovered_at": self.recovered_at,
            "status": self.status,
            "peak_risk": round(self.peak_risk, 2),
            "trigger": self.trigger,
            "actions_taken": ", ".join(self.actions_taken),
            "affected_requests": self.affected_requests,
            "blocked_requests": self.blocked_requests,
        }


class IncidentManager:
    def __init__(self, threshold: float = 60.0):
        self.threshold = threshold
        self.active_incident: Optional[IncidentState] = None
        self.incident_history: List[IncidentState] = []
        self._lock = Lock()
        self._normal_streak = 0

    def evaluate(
        self,
        session_id: str,
        risk_score: float,
        prediction: str,
        defense_level: str,
        action: str,
        total_requests: int,
        blocked_requests: int,
    ) -> Optional[IncidentState]:
        now = time.time()
        with self._lock:
            # Condition for incident detection: risk exceeds threshold
            if risk_score >= self.threshold and self.active_incident is None:
                inc_id = f"INC-{int(now)%100000:05d}"
                severity = "HIGH" if risk_score >= 80.0 else "SUSPICIOUS"
                self.active_incident = IncidentState(
                    incident_id=inc_id,
                    session_id=session_id,
                    severity=severity,
                    description=f"Volumetric anomaly detected by Isolation Forest (Risk: {risk_score:.1f})",
                    opened_at=now,
                    detected_at=now,
                    defense_started_at=now,
                    recovered_at=None,
                    status="ACTIVE",
                    peak_risk=risk_score,
                    trigger=f"Risk score {risk_score:.1f} crossed threshold {self.threshold:.1f}",
                    actions_taken=[action],
                    affected_requests=total_requests,
                    blocked_requests=blocked_requests,
                )
                self._normal_streak = 0
                return self.active_incident

            elif self.active_incident is not None:
                inc = self.active_incident
                inc.peak_risk = max(inc.peak_risk, risk_score)
                inc.affected_requests = total_requests
                inc.blocked_requests = blocked_requests

                if action not in inc.actions_taken:
                    inc.actions_taken.append(action)

                # Escalation if risk reaches critical high
                if risk_score >= 85.0 and inc.status != "ESCALATED":
                    inc.status = "ESCALATED"
                    inc.severity = "CRITICAL"

                # Recovery check: sustained normal risk
                if risk_score < self.threshold:
                    self._normal_streak += 1
                    if self._normal_streak >= 2:
                        inc.status = "MITIGATING"
                    if self._normal_streak >= 4:
                        inc.status = "RECOVERED"
                        inc.recovered_at = now
                        save_incident(inc.to_dict())
                        self.incident_history.append(inc)
                        self.active_incident = None
                else:
                    self._normal_streak = 0
                    if inc.status == "MITIGATING":
                        inc.status = "ACTIVE"

                return inc

            return None

    def finalize(self, session_id: str):
        with self._lock:
            if self.active_incident:
                self.active_incident.status = "RECOVERED"
                self.active_incident.recovered_at = time.time()
                save_incident(self.active_incident.to_dict())
                self.incident_history.append(self.active_incident)
                self.active_incident = None

    def reset(self):
        with self._lock:
            self.active_incident = None
            self.incident_history.clear()
            self._normal_streak = 0

    def get_status(self) -> Dict:
        with self._lock:
            if self.active_incident:
                return {
                    "has_active_incident": True,
                    "status": self.active_incident.status,
                    "incident_id": self.active_incident.incident_id,
                    "severity": self.active_incident.severity,
                }
            return {
                "has_active_incident": False,
                "status": "MONITORING",
                "total_recorded": len(self.incident_history),
            }


incident_manager = IncidentManager()
