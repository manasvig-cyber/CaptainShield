"""
AegisGuard - ML Defense Controller

Connects the Isolation Forest anomaly detector to the
adaptive defense engine.

Controlled local laboratory use only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from adaptive_defense import (
    AdaptiveDefenseEngine,
    DefenseDecision,
)
from ml_detector import (
    AnomalyResult,
    MLAnomalyDetector,
)


@dataclass(frozen=True)
class MLDefenseResult:
    """
    Combined result produced by the ML detector and adaptive defense.
    """

    client_id: str
    prediction: str
    risk_score: float
    risk_level: str
    defense_level: str
    defense_action: str
    blocked: bool
    max_requests: int
    window_seconds: float
    reason: str


class MLDefenseController:
    """
    Orchestrates:

        Feature Vector
             ↓
        ML Detector
             ↓
        Risk Score
             ↓
        Adaptive Defense
             ↓
        Defense Decision
    """

    def __init__(
        self,
        detector: MLAnomalyDetector,
        defense_engine: AdaptiveDefenseEngine,
    ) -> None:
        if not isinstance(detector, MLAnomalyDetector):
            raise TypeError(
                "detector must be an MLAnomalyDetector instance."
            )

        if not isinstance(
            defense_engine,
            AdaptiveDefenseEngine,
        ):
            raise TypeError(
                "defense_engine must be an AdaptiveDefenseEngine instance."
            )

        self.detector = detector
        self.defense_engine = defense_engine

    def analyze_and_defend(
        self,
        client_id: str,
        feature_vector: Sequence[float],
    ) -> MLDefenseResult:
        """
        Run the trained ML model and immediately apply its
        risk score to the adaptive defense engine.
        """

        if not client_id or not client_id.strip():
            raise ValueError(
                "client_id must not be empty."
            )

        if not self.detector.is_fitted:
            raise RuntimeError(
                "ML detector must be fitted before inference."
            )

        normalized_client_id = client_id.strip()

        # ---------------------------------------------------------------------
        # 1. REAL ML INFERENCE
        # ---------------------------------------------------------------------

        anomaly_result: AnomalyResult = self.detector.predict(
            feature_vector
        )

        # ---------------------------------------------------------------------
        # 2. ML RISK → ADAPTIVE DEFENSE
        # ---------------------------------------------------------------------

        defense_result: DefenseDecision = (
            self.defense_engine.evaluate(
                client_id=normalized_client_id,
                risk_score=anomaly_result.risk_score,
            )
        )

        # ---------------------------------------------------------------------
        # 3. COMBINED RESULT
        # ---------------------------------------------------------------------

        return MLDefenseResult(
            client_id=normalized_client_id,
            prediction=anomaly_result.prediction,
            risk_score=anomaly_result.risk_score,
            risk_level=anomaly_result.risk_level,
            defense_level=defense_result.level.value,
            defense_action=defense_result.action,
            blocked=defense_result.blocked,
            max_requests=defense_result.max_requests,
            window_seconds=defense_result.window_seconds,
            reason=defense_result.reason,
        )

    def apply_anomaly_result(
        self,
        client_id: str,
        anomaly_result: AnomalyResult,
    ) -> MLDefenseResult:
        """
        Apply an already-computed ML result to adaptive defense.

        This method is useful when another component already performed
        ML inference and we only need to connect the result to defense.
        """

        if not client_id or not client_id.strip():
            raise ValueError(
                "client_id must not be empty."
            )

        normalized_client_id = client_id.strip()

        defense_result = self.defense_engine.evaluate(
            client_id=normalized_client_id,
            risk_score=anomaly_result.risk_score,
        )

        return MLDefenseResult(
            client_id=normalized_client_id,
            prediction=anomaly_result.prediction,
            risk_score=anomaly_result.risk_score,
            risk_level=anomaly_result.risk_level,
            defense_level=defense_result.level.value,
            defense_action=defense_result.action,
            blocked=defense_result.blocked,
            max_requests=defense_result.max_requests,
            window_seconds=defense_result.window_seconds,
            reason=defense_result.reason,
        )