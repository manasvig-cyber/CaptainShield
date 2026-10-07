from __future__ import annotations

from dataclasses import dataclass
from threading import Event, Lock, Thread
from time import monotonic
from typing import Optional

import requests

from simulator import SimulationEngine
from telemetry import TelemetryCollector


# =============================================================================
# LIVE ML ANALYSIS SNAPSHOT
# =============================================================================

@dataclass(frozen=True, slots=True)
class LiveMLSnapshot:
    """
    Immutable snapshot of one live ML analysis cycle.
    """

    timestamp: float
    request_count: int
    active_clients: int

    requests_per_second: float
    average_inter_request_time: float
    burst_ratio: float
    rate_limit_ratio: float
    error_ratio: float
    average_response_time_ms: float

    analyzed_clients: int
    highest_risk_score: float
    highest_risk_level: str
    highest_prediction: str


# =============================================================================
# LIVE ML DEFENSE MONITOR
# =============================================================================

class LiveMLDefenseMonitor:
    """
    Live telemetry → ML → adaptive-defense monitor.

    The monitor runs beside a SimulationEngine.

    Responsibilities:
        1. drain simulator events
        2. ingest request telemetry
        3. build the seven-feature ML vector
        4. send the vector to the Flask ML endpoint
        5. apply the resulting ML decision to active simulated clients

    The Flask application remains the owner of:
        - the validated ML model
        - AdaptiveDefenseEngine
        - rate-limit policies
        - temporary restrictions

    This keeps the monitoring layer separate from the server-side
    enforcement layer.

    The telemetry window is intentionally set to 2 seconds because
    the validated ML model was evaluated using 2-second feature windows.
    """

    def __init__(
        self,
        engine: SimulationEngine,
        server_url: str = "http://127.0.0.1:5000",
        *,
        telemetry_window_seconds: float = 2.0,
        analysis_interval_seconds: float = 2.0,
        request_timeout_seconds: float = 3.0,
    ) -> None:

        if not isinstance(
            engine,
            SimulationEngine,
        ):
            raise TypeError(
                "engine must be a SimulationEngine instance."
            )

        if not server_url or not server_url.strip():
            raise ValueError(
                "server_url cannot be empty."
            )

        if telemetry_window_seconds <= 0:
            raise ValueError(
                "telemetry_window_seconds must be greater than zero."
            )

        if analysis_interval_seconds <= 0:
            raise ValueError(
                "analysis_interval_seconds must be greater than zero."
            )

        if request_timeout_seconds <= 0:
            raise ValueError(
                "request_timeout_seconds must be greater than zero."
            )

        self.engine = engine

        self.server_url = server_url.rstrip(
            "/"
        )

        self.telemetry_window_seconds = float(
            telemetry_window_seconds
        )

        self.analysis_interval_seconds = float(
            analysis_interval_seconds
        )

        self.request_timeout_seconds = float(
            request_timeout_seconds
        )

        self.telemetry = TelemetryCollector(
            window_seconds=self.telemetry_window_seconds
        )

        self._stop_event = Event()

        self._thread: Optional[Thread] = None

        self._state_lock = Lock()

        self._latest_snapshot: LiveMLSnapshot | None = None

        self._analysis_count = 0

        self._last_error: str | None = None

    # =========================================================================
    # STATUS
    # =========================================================================

    @property
    def is_running(self) -> bool:
        """
        Return True while the monitor thread is active.
        """

        return (
            self._thread is not None
            and self._thread.is_alive()
        )

    @property
    def analysis_count(self) -> int:
        """
        Return the number of completed ML analysis cycles.
        """

        with self._state_lock:
            return self._analysis_count

    @property
    def last_error(self) -> str | None:
        """
        Return the latest monitor error, if any.
        """

        with self._state_lock:
            return self._last_error

    # =========================================================================
    # START
    # =========================================================================

    def start(self) -> None:
        """
        Start the live monitoring thread.

        The SimulationEngine must already be running.
        """

        if not self.engine.is_running:
            raise RuntimeError(
                "SimulationEngine must be running before "
                "LiveMLDefenseMonitor.start()."
            )

        if self.is_running:
            raise RuntimeError(
                "Live ML monitor is already running."
            )

        self._stop_event.clear()

        self.telemetry.reset()

        with self._state_lock:
            self._latest_snapshot = None
            self._analysis_count = 0
            self._last_error = None

        self._thread = Thread(
            target=self._monitor_loop,
            name="aegis-live-ml-monitor",
            daemon=True,
        )

        self._thread.start()

    # =========================================================================
    # STOP
    # =========================================================================

    def stop(
        self,
        *,
        timeout_seconds: float = 5.0,
    ) -> None:
        """
        Stop the monitor thread cleanly.
        """

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(
                timeout=timeout_seconds
            )

        self._thread = None

    # =========================================================================
    # SNAPSHOT
    # =========================================================================

    def snapshot(self) -> LiveMLSnapshot | None:
        """
        Return the latest completed ML analysis snapshot.
        """

        with self._state_lock:
            return self._latest_snapshot

    # =========================================================================
    # MONITOR LOOP
    # =========================================================================

    def _monitor_loop(self) -> None:
        """
        Main live monitoring loop.
        """

        next_analysis = monotonic()

        while not self._stop_event.is_set():

            # -----------------------------------------------------------------
            # Drain newly generated simulator events.
            # -----------------------------------------------------------------

            events = self.engine.drain_events()

            for event in events:
                self.telemetry.ingest(
                    event
                )

            # -----------------------------------------------------------------
            # Run ML analysis at the configured interval.
            # -----------------------------------------------------------------

            current_time = monotonic()

            if current_time >= next_analysis:

                try:
                    self._run_analysis_cycle()

                except Exception as exc:
                    with self._state_lock:
                        self._last_error = (
                            f"{type(exc).__name__}: {exc}"
                        )

                next_analysis = (
                    current_time
                    + self.analysis_interval_seconds
                )

            # -----------------------------------------------------------------
            # Small wait to avoid a busy loop.
            # -----------------------------------------------------------------

            self._stop_event.wait(
                min(
                    0.20,
                    self.analysis_interval_seconds,
                )
            )

    # =========================================================================
    # ANALYSIS CYCLE
    # =========================================================================

    def _run_analysis_cycle(self) -> None:
        """
        Build a live feature vector and send it to Flask.

        The current Isolation Forest model operates on an aggregate traffic
        window. Therefore, the resulting network-level risk decision is
        applied to the logical clients active in the current telemetry
        window.

        The system does not claim that the aggregate model has identified
        one specific attacker.
        """

        features = self.telemetry.calculate_features(
            rolling=True
        )

        if features.request_count == 0:
            return

        feature_vector = features.as_vector()

        # ---------------------------------------------------------------------
        # Determine which logical clients are active in this window.
        # ---------------------------------------------------------------------

        observations = self.telemetry.snapshot()

        active_clients = {
            observation.client_id
            for observation in observations
            if observation.client_id
        }

        if not active_clients:
            return

        # ---------------------------------------------------------------------
        # Apply the real ML analysis through Flask.
        # ---------------------------------------------------------------------

        results: list[dict] = []

        highest_risk_score = 0.0
        highest_risk_level = "NORMAL"
        highest_prediction = "NORMAL"

        for client_id in sorted(
            active_clients
        ):

            response = requests.post(
                f"{self.server_url}/lab/ml/analyze",
                json={
                    "client": client_id,
                    "features": feature_vector,
                },
                timeout=self.request_timeout_seconds,
            )

            response.raise_for_status()

            result = response.json()

            results.append(result)

            risk_score = float(
                result.get(
                    "risk_score",
                    0.0,
                )
            )

            if risk_score >= highest_risk_score:
                highest_risk_score = risk_score
                highest_risk_level = str(
                    result.get(
                        "risk_level",
                        "NORMAL",
                    )
                )
                highest_prediction = str(
                    result.get(
                        "prediction",
                        "NORMAL",
                    )
                )

        # ---------------------------------------------------------------------
        # Store an immutable analysis snapshot.
        # ---------------------------------------------------------------------

        snapshot = LiveMLSnapshot(
            timestamp=monotonic(),

            request_count=features.request_count,
            active_clients=features.active_clients,

            requests_per_second=(
                features.requests_per_second
            ),

            average_inter_request_time=(
                features.average_inter_request_time
            ),

            burst_ratio=features.burst_ratio,

            rate_limit_ratio=(
                features.rate_limit_ratio
            ),

            error_ratio=features.error_ratio,

            average_response_time_ms=(
                features.average_response_time_ms
            ),

            analyzed_clients=len(results),

            highest_risk_score=(
                highest_risk_score
            ),

            highest_risk_level=(
                highest_risk_level
            ),

            highest_prediction=(
                highest_prediction
            ),
        )

        with self._state_lock:
            self._latest_snapshot = snapshot
            self._analysis_count += 1
            self._last_error = None

    # =========================================================================
    # RESET
    # =========================================================================

    def reset(self) -> None:
        """
        Reset telemetry and monitor state.
        """

        self.telemetry.reset()

        with self._state_lock:
            self._latest_snapshot = None
            self._analysis_count = 0
            self._last_error = None


# =============================================================================
# CONTROLLED SESSION HELPER
# =============================================================================

def run_controlled_session(
    *,
    target_url: str = "http://127.0.0.1:5000/",
    num_threads: int = 5,
    request_interval_seconds: float = 0.0,
    request_interval_jitter_seconds: float = 0.0,
    random_seed: int = 42,
    duration_seconds: float = 20.0,
    telemetry_window_seconds: float = 2.0,
    analysis_interval_seconds: float = 2.0,
) -> tuple[
    SimulationEngine,
    LiveMLDefenseMonitor,
]:
    """
    Run one controlled simulation while live ML defense is active.

    The telemetry window defaults to 2 seconds to match the feature
    window used during model evaluation.

    Returns the completed engine and monitor so their final state can
    be inspected by the caller.
    """

    if duration_seconds <= 0:
        raise ValueError(
            "duration_seconds must be greater than zero."
        )

    engine = SimulationEngine(
        target_url,
        num_threads=num_threads,
        request_interval_seconds=(
            request_interval_seconds
        ),
        request_interval_jitter_seconds=(
            request_interval_jitter_seconds
        ),
        random_seed=random_seed,
    )

    monitor = LiveMLDefenseMonitor(
        engine,
        telemetry_window_seconds=(
            telemetry_window_seconds
        ),
        analysis_interval_seconds=(
            analysis_interval_seconds
        ),
    )

    engine.start()
    monitor.start()

    try:
        Event().wait(
            timeout=duration_seconds
        )

    finally:
        monitor.stop()
        engine.stop()

    return engine, monitor