from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from statistics import mean
from threading import Lock
from time import monotonic
from typing import Deque, Mapping


# =============================================================================
# ML FEATURE MODEL
# =============================================================================

@dataclass(frozen=True, slots=True)
class TrafficFeatures:
    """
    Immutable ML-ready representation of a traffic observation window.

    The feature order is intentionally fixed because the same order must be
    used during both model training and inference.
    """

    window_seconds: float

    request_count: int
    requests_per_second: float

    average_inter_request_time: float

    burst_ratio: float

    success_ratio: float
    rate_limit_ratio: float
    error_ratio: float

    average_response_time_ms: float

    active_clients: int

    def as_vector(self) -> list[float]:
        """
        Return the numerical feature vector used by the ML model.

        IMPORTANT:
        Do not change this order after model training begins.
        """

        return [
            self.requests_per_second,
            self.average_inter_request_time,
            self.burst_ratio,
            self.rate_limit_ratio,
            self.error_ratio,
            self.average_response_time_ms,
            float(self.active_clients),
        ]

    @classmethod
    def feature_names(cls) -> tuple[str, ...]:
        """
        Return the canonical feature names in model-input order.
        """

        return (
            "requests_per_second",
            "average_inter_request_time",
            "burst_ratio",
            "rate_limit_ratio",
            "error_ratio",
            "average_response_time_ms",
            "active_clients",
        )


# =============================================================================
# INTERNAL REQUEST RECORD
# =============================================================================

@dataclass(slots=True)
class _RequestObservation:
    """
    Internal representation of one observed request.

    This is intentionally separate from TrafficFeatures so that raw events
    remain available for feature engineering.
    """

    timestamp: float
    status_code: int
    response_ms: float
    client_id: str


# =============================================================================
# TELEMETRY COLLECTOR
# =============================================================================

class TelemetryCollector:
    """
    Thread-safe telemetry collector for the controlled local simulator.

    Responsibilities:
        - ingest simulator request events
        - retain recent observations
        - calculate traffic statistics
        - produce an ML-ready feature vector

    The collector has no dependency on:
        - Flask
        - Tkinter
        - scikit-learn
        - GUI code

    This keeps the telemetry layer reusable by the ML engine and GUI.
    """

    def __init__(
        self,
        *,
        window_seconds: float = 5.0,
        max_observations: int = 100_000,
    ) -> None:

        if window_seconds <= 0:
            raise ValueError(
                "window_seconds must be greater than zero"
            )

        if max_observations <= 0:
            raise ValueError(
                "max_observations must be greater than zero"
            )

        self.window_seconds = float(window_seconds)
        self.max_observations = int(max_observations)

        self._requests: Deque[_RequestObservation] = deque(
            maxlen=self.max_observations
        )

        self._lock = Lock()

    # =========================================================================
    # EVENT INGESTION
    # =========================================================================

    def ingest(
        self,
        event: Mapping[str, object],
    ) -> None:
        """
        Ingest one simulator event.

        Only completed HTTP request events are converted into telemetry
        observations.

        Expected request event structure:

        {
            "type": "request",
            "timestamp": ...,
            "client_id": "sim-worker-1",
            "status_code": 200,
            "response_ms": 12.4
        }
        """

        if event.get("type") != "request":
            return

        status_code = event.get("status_code")
        response_ms = event.get("response_ms")
        timestamp = event.get("timestamp")
        client_id = event.get("client_id")

        # ---------------------------------------------------------------------
        # Validate event fields
        # ---------------------------------------------------------------------

        if not isinstance(status_code, int):
            return

        if not isinstance(response_ms, (int, float)):
            return

        if not isinstance(timestamp, (int, float)):
            return

        if not isinstance(client_id, str) or not client_id:
            client_id = "unknown"

        # Reject impossible negative measurements.
        if response_ms < 0:
            return

        observation = _RequestObservation(
            timestamp=float(timestamp),
            status_code=status_code,
            response_ms=float(response_ms),
            client_id=client_id,
        )

        with self._lock:

            self._requests.append(observation)

            # Only perform pruning against the event's own timestamp here.
            # This prevents offline/session ingestion from losing valid data
            # simply because the queue took time to process.
            self._prune(
                now=float(timestamp)
            )

    # =========================================================================
    # FEATURE CALCULATION
    # =========================================================================

    def calculate_features(
        self,
        *,
        now: float | None = None,
        rolling: bool = False,
    ) -> TrafficFeatures:
        """
        Calculate the current ML feature vector.

        Parameters
        ----------
        now:
            Optional reference time.

            When omitted:
                The newest observed event timestamp is used.

            This makes offline/session analysis deterministic.

        rolling:
            When True:
                Use the actual current monotonic clock and enforce a live
                rolling window.

            When False:
                Use the newest observed event timestamp. This is preferred
                for post-session analysis and testing.

        Returns
        -------
        TrafficFeatures
            Structured feature set ready for ML processing.
        """

        with self._lock:

            if not self._requests:
                return self._empty_features()

            # -----------------------------------------------------------------
            # Determine analysis timestamp
            # -----------------------------------------------------------------

            if now is not None:

                analysis_time = float(now)

            elif rolling:

                analysis_time = monotonic()

            else:

                # Offline/session mode:
                # anchor analysis to the newest observed event.
                analysis_time = max(
                    observation.timestamp
                    for observation in self._requests
                )

            # -----------------------------------------------------------------
            # Remove observations outside the active window
            # -----------------------------------------------------------------

            self._prune(
                now=analysis_time
            )

            observations = list(self._requests)

        # ---------------------------------------------------------------------
        # No observations remain
        # ---------------------------------------------------------------------

        if not observations:
            return self._empty_features()

        request_count = len(observations)

        # =========================================================================
        # REQUEST RATE
        # =========================================================================

        requests_per_second = (
            request_count
            / self.window_seconds
        )

        # =========================================================================
        # INTER-REQUEST TIMING
        # =========================================================================

        timestamps = sorted(
            observation.timestamp
            for observation in observations
        )

        intervals = [
            current - previous
            for previous, current in zip(
                timestamps,
                timestamps[1:],
            )
            if current >= previous
        ]

        average_inter_request_time = (
            mean(intervals)
            if intervals
            else 0.0
        )

        # =========================================================================
        # BURST ANALYSIS
        # =========================================================================

        second_buckets = Counter(
            int(observation.timestamp)
            for observation in observations
        )

        peak_requests_per_second = (
            max(second_buckets.values())
            if second_buckets
            else 0
        )

        if requests_per_second > 0:
            burst_ratio = (
                peak_requests_per_second
                / requests_per_second
            )
        else:
            burst_ratio = 0.0

        # Keep the feature bounded.
        burst_ratio = min(
            max(burst_ratio, 0.0),
            10.0,
        )

        # =========================================================================
        # HTTP RESPONSE DISTRIBUTION
        # =========================================================================

        successful = sum(
            observation.status_code == 200
            for observation in observations
        )

        rate_limited = sum(
            observation.status_code == 429
            for observation in observations
        )

        failed = sum(
            observation.status_code not in (200, 429)
            for observation in observations
        )

        success_ratio = (
            successful / request_count
        )

        rate_limit_ratio = (
            rate_limited / request_count
        )

        error_ratio = (
            failed / request_count
        )

        # =========================================================================
        # RESPONSE TIME
        # =========================================================================

        average_response_time_ms = mean(
            observation.response_ms
            for observation in observations
        )

        # =========================================================================
        # ACTIVE SIMULATED CLIENTS
        # =========================================================================

        active_clients = len(
            {
                observation.client_id
                for observation in observations
            }
        )

        # =========================================================================
        # RETURN STRUCTURED FEATURE SET
        # =========================================================================

        return TrafficFeatures(
            window_seconds=self.window_seconds,

            request_count=request_count,
            requests_per_second=requests_per_second,

            average_inter_request_time=(
                average_inter_request_time
            ),

            burst_ratio=burst_ratio,

            success_ratio=success_ratio,
            rate_limit_ratio=rate_limit_ratio,
            error_ratio=error_ratio,

            average_response_time_ms=(
                average_response_time_ms
            ),

            active_clients=active_clients,
        )

    # =========================================================================
    # EMPTY FEATURE FACTORY
    # =========================================================================

    def _empty_features(self) -> TrafficFeatures:
        """
        Return a valid zero-valued feature set.

        This avoids duplicating the same structure throughout the collector.
        """

        return TrafficFeatures(
            window_seconds=self.window_seconds,

            request_count=0,
            requests_per_second=0.0,

            average_inter_request_time=0.0,

            burst_ratio=0.0,

            success_ratio=0.0,
            rate_limit_ratio=0.0,
            error_ratio=0.0,

            average_response_time_ms=0.0,

            active_clients=0,
        )

    # =========================================================================
    # MAINTENANCE
    # =========================================================================

    def reset(self) -> None:
        """
        Remove all telemetry observations.
        """

        with self._lock:
            self._requests.clear()

    def observation_count(self) -> int:
        """
        Return the current number of stored observations.
        """

        with self._lock:
            return len(self._requests)

    def snapshot(self) -> tuple[_RequestObservation, ...]:
        """
        Return a read-only snapshot of the current raw observations.

        Useful for debugging, session analysis, and future incident
        processing without exposing the internal deque itself.
        """

        with self._lock:
            return tuple(self._requests)

    # =========================================================================
    # WINDOW MAINTENANCE
    # =========================================================================

    def _prune(
        self,
        *,
        now: float,
    ) -> None:
        """
        Remove observations older than the active telemetry window.
        """

        cutoff = now - self.window_seconds

        while (
            self._requests
            and self._requests[0].timestamp < cutoff
        ):
            self._requests.popleft()