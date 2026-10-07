"""
AegisGuard - Incident Analysis Engine

Converts live ML and adaptive-defense observations into structured
security incident records for the GUI and reporting layer.

Controlled local laboratory use only.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Optional


# =============================================================================
# INCIDENT RECORD
# =============================================================================

@dataclass(frozen=True, slots=True)
class IncidentRecord:
    """
    Immutable representation of one detected security incident.
    """

    incident_id: str
    timestamp: float

    prediction: str
    risk_score: float
    risk_level: str

    defense_level: str
    defense_action: str

    request_count: int
    requests_per_second: float
    active_clients: int

    rate_limit_ratio: float
    error_ratio: float
    average_response_time_ms: float

    affected_clients: tuple[str, ...]

    status: str
    summary: str


# =============================================================================
# INCIDENT ANALYZER
# =============================================================================

class IncidentAnalyzer:
    """
    Converts live ML-defense results into structured incident records.

    The analyzer is intentionally independent of:
        - Flask
        - Tkinter
        - scikit-learn
        - simulator internals

    This allows the same incident records to be consumed by:
        - GUI
        - logs
        - reports
        - future persistence
    """

    def __init__(
        self,
        *,
        incident_risk_threshold: float = 60.0,
    ) -> None:

        if not 0.0 <= incident_risk_threshold <= 100.0:
            raise ValueError(
                "incident_risk_threshold must be between 0 and 100."
            )

        self.incident_risk_threshold = float(
            incident_risk_threshold
        )

        self._counter = 0

        self._active_incident: Optional[IncidentRecord] = None

    # =========================================================================
    # ANALYZE
    # =========================================================================

    def analyze(
        self,
        *,
        prediction: str,
        risk_score: float,
        risk_level: str,
        defense_level: str,
        defense_action: str,
        request_count: int,
        requests_per_second: float,
        active_clients: int,
        rate_limit_ratio: float,
        error_ratio: float,
        average_response_time_ms: float,
        affected_clients: tuple[str, ...] = (),
    ) -> IncidentRecord | None:
        """
        Create an incident record when the supplied ML risk indicates
        suspicious or anomalous traffic.

        Returns None when the observation is below the incident threshold.
        """

        normalized_prediction = str(
            prediction
        ).upper()

        normalized_risk = max(
            0.0,
            min(
                100.0,
                float(risk_score),
            ),
        )

        normalized_risk_level = str(
            risk_level
        ).upper()

        normalized_defense_level = str(
            defense_level
        ).upper()

        normalized_defense_action = str(
            defense_action
        ).upper()

        if normalized_risk < self.incident_risk_threshold:
            return None

        self._counter += 1

        incident_id = (
            f"INC-{self._counter:04d}"
        )

        now = monotonic()

        severity = self._derive_severity(
            normalized_risk,
            normalized_risk_level,
        )

        summary = self._build_summary(
            severity=severity,
            prediction=normalized_prediction,
            risk_score=normalized_risk,
            defense_level=normalized_defense_level,
            defense_action=normalized_defense_action,
            requests_per_second=float(
                requests_per_second
            ),
            active_clients=int(
                active_clients
            ),
        )

        incident = IncidentRecord(
            incident_id=incident_id,
            timestamp=now,

            prediction=normalized_prediction,
            risk_score=normalized_risk,
            risk_level=normalized_risk_level,

            defense_level=normalized_defense_level,
            defense_action=normalized_defense_action,

            request_count=max(
                0,
                int(request_count),
            ),

            requests_per_second=max(
                0.0,
                float(requests_per_second),
            ),

            active_clients=max(
                0,
                int(active_clients),
            ),

            rate_limit_ratio=max(
                0.0,
                min(
                    1.0,
                    float(rate_limit_ratio),
                ),
            ),

            error_ratio=max(
                0.0,
                min(
                    1.0,
                    float(error_ratio),
                ),
            ),

            average_response_time_ms=max(
                0.0,
                float(
                    average_response_time_ms
                ),
            ),

            affected_clients=tuple(
                affected_clients
            ),

            status="OPEN",

            summary=summary,
        )

        self._active_incident = incident

        return incident

    # =========================================================================
    # SEVERITY
    # =========================================================================

    def _derive_severity(
        self,
        risk_score: float,
        risk_level: str,
    ) -> str:
        """
        Derive a descriptive incident severity from the ML result.
        """

        if (
            risk_level == "HIGH_RISK"
            or risk_score >= 80.0
        ):
            return "HIGH"

        if (
            risk_level == "SUSPICIOUS"
            or risk_score >= 60.0
        ):
            return "MEDIUM"

        return "LOW"

    # =========================================================================
    # SUMMARY
    # =========================================================================

    def _build_summary(
        self,
        *,
        severity: str,
        prediction: str,
        risk_score: float,
        defense_level: str,
        defense_action: str,
        requests_per_second: float,
        active_clients: int,
    ) -> str:
        """
        Build a human-readable incident summary.
        """

        return (
            f"{severity} severity {prediction.lower()} traffic detected "
            f"with ML risk score {risk_score:.2f}. "
            f"Traffic rate: {requests_per_second:.2f} requests/sec "
            f"across {active_clients} active client(s). "
            f"Adaptive defense state: {defense_level}. "
            f"Action: {defense_action}."
        )

    # =========================================================================
    # RECOVERY
    # =========================================================================

    def mark_recovered(self) -> IncidentRecord | None:
        """
        Mark the current incident as recovered.
        """

        if self._active_incident is None:
            return None

        incident = self._active_incident

        recovered = IncidentRecord(
            incident_id=incident.incident_id,
            timestamp=incident.timestamp,

            prediction=incident.prediction,
            risk_score=incident.risk_score,
            risk_level=incident.risk_level,

            defense_level=incident.defense_level,
            defense_action=incident.defense_action,

            request_count=incident.request_count,
            requests_per_second=(
                incident.requests_per_second
            ),
            active_clients=incident.active_clients,

            rate_limit_ratio=(
                incident.rate_limit_ratio
            ),
            error_ratio=incident.error_ratio,

            average_response_time_ms=(
                incident.average_response_time_ms
            ),

            affected_clients=(
                incident.affected_clients
            ),

            status="RECOVERED",

            summary=(
                incident.summary
                + " Incident marked as recovered."
            ),
        )

        self._active_incident = None

        return recovered

    # =========================================================================
    # CURRENT INCIDENT
    # =========================================================================

    def current_incident(self) -> IncidentRecord | None:
        """
        Return the currently active incident, if any.
        """

        return self._active_incident

    # =========================================================================
    # RESET
    # =========================================================================

    def reset(self) -> None:
        """
        Clear the current incident state.
        """

        self._active_incident = None
        self._counter = 0