from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from sklearn.ensemble import IsolationForest

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from sklearn.model_selection import train_test_split


# =============================================================================
# ANOMALY RESULT
# =============================================================================

@dataclass(frozen=True, slots=True)
class AnomalyResult:
    """
    Result of one ML inference operation.
    """

    prediction: str
    risk_level: str
    risk_score: float

    raw_anomaly_score: float
    decision_threshold: float
    model_threshold: float

    feature_count: int

    @property
    def is_anomaly(self) -> bool:
        return self.prediction == "ANOMALY"


# =============================================================================
# EVALUATION RESULT
# =============================================================================

@dataclass(frozen=True, slots=True)
class MLEvaluationResult:
    """
    Evaluation result for normal and anomalous observations.
    """

    total_samples: int

    normal_samples: int
    anomaly_samples: int

    accuracy: float
    precision: float
    recall: float
    f1_score: float

    confusion_matrix: tuple[
        tuple[int, int],
        tuple[int, int],
    ]

    normal_correct: int
    normal_false_positive: int

    anomaly_correct: int
    anomaly_missed: int


# =============================================================================
# EVENT TIMING SUMMARY
# =============================================================================

@dataclass(frozen=True, slots=True)
class EventTimingSummary:
    """
    Timing summary for one recorded simulator session.
    """

    request_count: int

    first_timestamp: float | None
    last_timestamp: float | None

    duration_seconds: float

    estimated_requests_per_second: float


# =============================================================================
# ISOLATION FOREST DETECTOR
# =============================================================================

class MLAnomalyDetector:
    """
    Isolation Forest based traffic anomaly detector.

    Training flow:

        normal_fit
            ↓
        Isolation Forest
            ↓
        normal_calibration
            ↓
        calibrated decision threshold
            ↓
        unseen prediction

    Feature order:

        1. requests_per_second
        2. average_inter_request_time
        3. burst_ratio
        4. rate_limit_ratio
        5. error_ratio
        6. average_response_time_ms
        7. active_clients
    """

    FEATURE_COUNT = 7

    FEATURE_NAMES = (
        "requests_per_second",
        "average_inter_request_time",
        "burst_ratio",
        "rate_limit_ratio",
        "error_ratio",
        "average_response_time_ms",
        "active_clients",
    )

    def __init__(
        self,
        *,
        n_estimators: int = 300,
        contamination: str | float = "auto",
        random_state: int = 42,
        target_false_positive_rate: float = 0.05,
    ) -> None:

        if n_estimators <= 0:
            raise ValueError(
                "n_estimators must be greater than zero"
            )

        if not (
            0.001
            <= target_false_positive_rate
            <= 0.20
        ):
            raise ValueError(
                "target_false_positive_rate must be "
                "between 0.001 and 0.20"
            )

        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )

        self.random_state = int(
            random_state
        )

        self.target_false_positive_rate = float(
            target_false_positive_rate
        )

        self._is_fitted = False

        self._decision_threshold = 0.0

        self._model_threshold = 0.0

        self._calibration_q05 = 0.0
        self._calibration_q50 = 0.0
        self._calibration_q95 = 0.0

    # =========================================================================
    # TRAINING
    # =========================================================================

    def fit(
        self,
        normal_fit_vectors: Iterable[Sequence[float]],
        calibration_vectors: Iterable[Sequence[float]] | None = None,
    ) -> None:
        """
        Train Isolation Forest on normal traffic.

        If calibration data is provided, use it to determine a custom
        anomaly threshold rather than relying exclusively on the
        model's default threshold.
        """

        training_matrix = self._prepare_matrix(
            normal_fit_vectors
        )

        if training_matrix.shape[0] < 50:
            raise ValueError(
                "At least 50 normal training observations are required."
            )

        self.model.fit(
            training_matrix
        )

        self._model_threshold = float(
            self.model.offset_
        )

        if calibration_vectors is None:

            calibration_matrix = (
                training_matrix
            )

        else:

            calibration_matrix = (
                self._prepare_matrix(
                    calibration_vectors
                )
            )

            if calibration_matrix.shape[0] < 20:
                raise ValueError(
                    "At least 20 normal calibration observations "
                    "are recommended."
                )

        calibration_scores = (
            self.model.decision_function(
                calibration_matrix
            )
        )

        # Lower decision_function values mean more anomalous.
        percentile = (
            self.target_false_positive_rate
            * 100.0
        )

        self._decision_threshold = float(
            np.percentile(
                calibration_scores,
                percentile,
            )
        )

        self._calibration_q05 = float(
            np.percentile(
                calibration_scores,
                5,
            )
        )

        self._calibration_q50 = float(
            np.percentile(
                calibration_scores,
                50,
            )
        )

        self._calibration_q95 = float(
            np.percentile(
                calibration_scores,
                95,
            )
        )

        self._is_fitted = True

    # =========================================================================
    # PREDICTION
    # =========================================================================

    def predict(
        self,
        vector: Sequence[float],
    ) -> AnomalyResult:
        """
        Classify one observation using the calibrated threshold.
        """

        self._ensure_fitted()

        matrix = self._prepare_matrix(
            [vector]
        )

        raw_score = float(
            self.model.decision_function(
                matrix
            )[0]
        )

        prediction = (
            "ANOMALY"
            if raw_score < self._decision_threshold
            else "NORMAL"
        )

        risk_score = (
            self._calculate_risk_score(
                raw_score
            )
        )

        risk_level = (
            self._risk_level(
                risk_score
            )
        )

        return AnomalyResult(
            prediction=prediction,
            risk_level=risk_level,
            risk_score=risk_score,
            raw_anomaly_score=raw_score,
            decision_threshold=(
                self._decision_threshold
            ),
            model_threshold=(
                self._model_threshold
            ),
            feature_count=self.FEATURE_COUNT,
        )

    # =========================================================================
    # BATCH PREDICTION
    # =========================================================================

    def predict_batch(
        self,
        vectors: Iterable[Sequence[float]],
    ) -> list[AnomalyResult]:
        """
        Predict a collection of observations.
        """

        matrix = self._prepare_matrix(
            vectors
        )

        return [
            self.predict(vector)
            for vector in matrix
        ]

    # =========================================================================
    # EVALUATION
    # =========================================================================

    def evaluate(
        self,
        *,
        normal_test_vectors: Iterable[Sequence[float]],
        anomaly_test_vectors: Iterable[Sequence[float]],
    ) -> MLEvaluationResult:
        """
        Evaluate on unseen normal and anomaly observations.
        """

        self._ensure_fitted()

        normal_matrix = self._prepare_matrix(
            normal_test_vectors
        )

        anomaly_matrix = self._prepare_matrix(
            anomaly_test_vectors
        )

        if normal_matrix.shape[0] == 0:
            raise ValueError(
                "Normal test set cannot be empty."
            )

        if anomaly_matrix.shape[0] == 0:
            raise ValueError(
                "Anomaly test set cannot be empty."
            )

        combined = np.vstack(
            [
                normal_matrix,
                anomaly_matrix,
            ]
        )

        raw_scores = (
            self.model.decision_function(
                combined
            )
        )

        predicted_labels = np.where(
            raw_scores
            < self._decision_threshold,
            1,
            0,
        )

        true_labels = np.concatenate(
            [
                np.zeros(
                    normal_matrix.shape[0],
                    dtype=int,
                ),
                np.ones(
                    anomaly_matrix.shape[0],
                    dtype=int,
                ),
            ]
        )

        accuracy = accuracy_score(
            true_labels,
            predicted_labels,
        )

        precision = precision_score(
            true_labels,
            predicted_labels,
            zero_division=0,
        )

        recall = recall_score(
            true_labels,
            predicted_labels,
            zero_division=0,
        )

        f1 = f1_score(
            true_labels,
            predicted_labels,
            zero_division=0,
        )

        matrix = confusion_matrix(
            true_labels,
            predicted_labels,
            labels=[0, 1],
        )

        return MLEvaluationResult(
            total_samples=len(
                true_labels
            ),

            normal_samples=(
                normal_matrix.shape[0]
            ),

            anomaly_samples=(
                anomaly_matrix.shape[0]
            ),

            accuracy=round(
                float(accuracy),
                4,
            ),

            precision=round(
                float(precision),
                4,
            ),

            recall=round(
                float(recall),
                4,
            ),

            f1_score=round(
                float(f1),
                4,
            ),

            confusion_matrix=(
                (
                    int(matrix[0, 0]),
                    int(matrix[0, 1]),
                ),
                (
                    int(matrix[1, 0]),
                    int(matrix[1, 1]),
                ),
            ),

            normal_correct=int(
                matrix[0, 0]
            ),

            normal_false_positive=int(
                matrix[0, 1]
            ),

            anomaly_correct=int(
                matrix[1, 1]
            ),

            anomaly_missed=int(
                matrix[1, 0]
            ),
        )

    # =========================================================================
    # MODEL STATUS
    # =========================================================================

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def decision_threshold(self) -> float:
        """
        Return the calibrated threshold.
        """

        if not self._is_fitted:
            raise RuntimeError(
                "Model has not been fitted."
            )

        return self._decision_threshold

    # =========================================================================
    # FEATURE VALIDATION
    # =========================================================================

    def _prepare_matrix(
        self,
        vectors: Iterable[Sequence[float]],
    ) -> np.ndarray:

        matrix = np.asarray(
            list(vectors),
            dtype=np.float64,
        )

        if matrix.ndim != 2:
            raise ValueError(
                "Feature input must be a 2-dimensional matrix."
            )

        if matrix.shape[0] == 0:
            return np.empty(
                (
                    0,
                    self.FEATURE_COUNT,
                ),
                dtype=np.float64,
            )

        if matrix.shape[1] != self.FEATURE_COUNT:
            raise ValueError(
                f"Expected {self.FEATURE_COUNT} features, "
                f"received {matrix.shape[1]}."
            )

        if not np.isfinite(matrix).all():
            raise ValueError(
                "Feature values must all be finite numbers."
            )

        return matrix

    # =========================================================================
    # RISK SCORE
    # =========================================================================

    def _calculate_risk_score(
        self,
        raw_score: float,
    ) -> float:
        """
        Convert the model score into an application-level 0-100 risk score.

        This is NOT an attack probability.
        """

        low = self._calibration_q05
        median = self._calibration_q50
        high = self._calibration_q95

        # Normal upper half.
        if raw_score >= median:

            span = high - median

            if span <= 1e-12:
                return 0.0

            score = (
                (high - raw_score)
                / span
                * 30.0
            )

            return round(
                float(
                    np.clip(
                        score,
                        0.0,
                        30.0,
                    )
                ),
                2,
            )

        # Normal-to-suspicious lower half.
        span = median - low

        if span <= 1e-12:
            return 50.0

        score = (
            30.0
            + (
                (median - raw_score)
                / span
            )
            * 70.0
        )

        return round(
            float(
                np.clip(
                    score,
                    0.0,
                    100.0,
                )
            ),
            2,
        )

    # =========================================================================
    # RISK LEVEL
    # =========================================================================

    @staticmethod
    def _risk_level(
        risk_score: float,
    ) -> str:

        if risk_score < 30:
            return "NORMAL"

        if risk_score < 60:
            return "WATCH"

        if risk_score < 80:
            return "SUSPICIOUS"

        return "HIGH_RISK"

    # =========================================================================
    # FIT CHECK
    # =========================================================================

    def _ensure_fitted(self) -> None:

        if not self._is_fitted:
            raise RuntimeError(
                "ML model has not been trained."
            )


# =============================================================================
# NORMAL DATASET SPLIT
# =============================================================================

def split_normal_dataset(
    normal_vectors: Sequence[Sequence[float]],
    *,
    calibration_size: float = 0.20,
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Split normal data into:

        training
        calibration
        test

    This is useful when only one normal dataset is available.

    For the final evaluation, separate simulation sessions are preferred.
    """

    matrix = np.asarray(
        normal_vectors,
        dtype=np.float64,
    )

    if matrix.ndim != 2:
        raise ValueError(
            "normal_vectors must be 2-dimensional."
        )

    if matrix.shape[1] != 7:
        raise ValueError(
            "normal_vectors must contain 7 features."
        )

    if matrix.shape[0] < 100:
        raise ValueError(
            "At least 100 normal samples are recommended."
        )

    if (
        calibration_size <= 0
        or test_size <= 0
        or calibration_size + test_size >= 1
    ):
        raise ValueError(
            "Invalid calibration/test sizes."
        )

    train_vectors, temporary_vectors = (
        train_test_split(
            matrix,
            test_size=(
                calibration_size
                + test_size
            ),
            random_state=random_state,
            shuffle=True,
        )
    )

    relative_test_size = (
        test_size
        / (
            calibration_size
            + test_size
        )
    )

    calibration_vectors, test_vectors = (
        train_test_split(
            temporary_vectors,
            test_size=relative_test_size,
            random_state=random_state,
            shuffle=True,
        )
    )

    return (
        np.asarray(train_vectors),
        np.asarray(calibration_vectors),
        np.asarray(test_vectors),
    )


# =============================================================================
# EVENT TIMING
# =============================================================================

def summarize_event_timing(
    events: Iterable[dict],
) -> EventTimingSummary:
    """
    Summarize the duration represented by request events.
    """

    timestamps = sorted(
        float(event["timestamp"])
        for event in events
        if (
            event.get("type") == "request"
            and isinstance(
                event.get("timestamp"),
                (int, float),
            )
        )
    )

    if not timestamps:

        return EventTimingSummary(
            request_count=0,
            first_timestamp=None,
            last_timestamp=None,
            duration_seconds=0.0,
            estimated_requests_per_second=0.0,
        )

    first_timestamp = timestamps[0]

    last_timestamp = timestamps[-1]

    duration_seconds = max(
        0.0,
        last_timestamp - first_timestamp,
    )

    estimated_rps = (
        len(timestamps)
        / duration_seconds
        if duration_seconds > 0
        else float(len(timestamps))
    )

    return EventTimingSummary(
        request_count=len(timestamps),
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
        duration_seconds=duration_seconds,
        estimated_requests_per_second=estimated_rps,
    )


# =============================================================================
# TELEMETRY → FEATURE VECTORS
# =============================================================================

def collect_feature_vectors_from_events(
    events: Iterable[dict],
    *,
    window_seconds: float = 2.0,
    step_seconds: float | None = None,
) -> np.ndarray:
    """
    Convert request events into NON-OVERLAPPING ML observation windows.

    By default:

        step_seconds == window_seconds

    This is intentionally non-overlapping to reduce evaluation leakage.
    """

    from telemetry import TelemetryCollector

    if window_seconds <= 0:
        raise ValueError(
            "window_seconds must be greater than zero."
        )

    if step_seconds is None:
        step_seconds = window_seconds

    if step_seconds <= 0:
        raise ValueError(
            "step_seconds must be greater than zero."
        )

    request_events = [
        event
        for event in events
        if (
            event.get("type") == "request"
            and isinstance(
                event.get("timestamp"),
                (int, float),
            )
        )
    ]

    if not request_events:

        return np.empty(
            (
                0,
                MLAnomalyDetector.FEATURE_COUNT,
            ),
            dtype=np.float64,
        )

    request_events.sort(
        key=lambda event: float(
            event["timestamp"]
        )
    )

    start_time = float(
        request_events[0]["timestamp"]
    )

    end_time = float(
        request_events[-1]["timestamp"]
    )

    if (
        end_time - start_time
        < window_seconds
    ):

        return np.empty(
            (
                0,
                MLAnomalyDetector.FEATURE_COUNT,
            ),
            dtype=np.float64,
        )

    vectors: list[list[float]] = []

    window_start = start_time

    while (
        window_start + window_seconds
        <= end_time + 1e-9
    ):

        window_end = (
            window_start
            + window_seconds
        )

        window_events = [
            event
            for event in request_events
            if (
                window_start
                <= float(event["timestamp"])
                < window_end
            )
        ]

        if window_events:

            collector = TelemetryCollector(
                window_seconds=window_seconds,
            )

            for event in window_events:
                collector.ingest(event)

            features = (
                collector.calculate_features()
            )

            if features.request_count > 0:

                vectors.append(
                    features.as_vector()
                )

        window_start += step_seconds

    if not vectors:

        return np.empty(
            (
                0,
                MLAnomalyDetector.FEATURE_COUNT,
            ),
            dtype=np.float64,
        )

    return np.asarray(
        vectors,
        dtype=np.float64,
    )


# =============================================================================
# DEVELOPMENT BOOTSTRAP DATASET
# =============================================================================

def build_bootstrap_normal_dataset(
    *,
    samples: int = 600,
    random_state: int = 42,
) -> np.ndarray:
    """
    Create synthetic normal traffic data for development only.

    Final evaluation should use simulator-derived traffic.
    """

    if samples < 50:
        raise ValueError(
            "At least 50 samples are required."
        )

    rng = np.random.default_rng(
        random_state
    )

    requests_per_second = np.clip(
        rng.normal(
            loc=10.0,
            scale=2.5,
            size=samples,
        ),
        2.0,
        20.0,
    )

    average_inter_request_time = np.clip(
        rng.normal(
            loc=0.10,
            scale=0.025,
            size=samples,
        ),
        0.03,
        0.30,
    )

    burst_ratio = np.clip(
        rng.normal(
            loc=1.25,
            scale=0.15,
            size=samples,
        ),
        1.0,
        2.0,
    )

    rate_limit_ratio = np.clip(
        rng.beta(
            1.5,
            35.0,
            size=samples,
        ),
        0.0,
        0.15,
    )

    error_ratio = np.clip(
        rng.beta(
            1.2,
            80.0,
            size=samples,
        ),
        0.0,
        0.08,
    )

    average_response_time_ms = np.clip(
        rng.normal(
            loc=120.0,
            scale=20.0,
            size=samples,
        ),
        60.0,
        220.0,
    )

    active_clients = rng.integers(
        1,
        6,
        size=samples,
    ).astype(np.float64)

    return np.column_stack(
        [
            requests_per_second,
            average_inter_request_time,
            burst_ratio,
            rate_limit_ratio,
            error_ratio,
            average_response_time_ms,
            active_clients,
        ]
    )