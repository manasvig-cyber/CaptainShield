from __future__ import annotations

import random
import uuid

from dataclasses import dataclass
from queue import Empty, Queue
from threading import Event, Lock, Thread, current_thread
from time import monotonic, perf_counter
from typing import Optional

import requests


# =============================================================================
# SIMULATION SNAPSHOT
# =============================================================================

@dataclass(frozen=True, slots=True)
class SimulationSnapshot:
    """
    Immutable snapshot of one simulation session.
    """

    requests_sent: int
    success_count: int
    rate_limited_count: int
    failed_count: int
    average_response_ms: float
    elapsed_seconds: float


# =============================================================================
# SIMULATION ENGINE
# =============================================================================

class SimulationEngine:
    """
    Controlled local traffic simulation engine.

    Each worker represents a logical simulated laboratory client.

    Features:
        - bounded worker threads
        - controlled request pacing
        - optional jitter
        - request timeout
        - thread-safe statistics
        - structured events
        - session IDs
        - clean queue handling
        - accurate shutdown timing
    """

    def __init__(
        self,
        target_url: str,
        num_threads: int = 5,
        *,
        timeout_seconds: float = 3.0,
        request_interval_seconds: float = 0.0,
        request_interval_jitter_seconds: float = 0.0,
        random_seed: int = 42,
        event_queue: Optional[Queue] = None,
    ) -> None:

        if not target_url or not target_url.strip():
            raise ValueError(
                "target_url cannot be empty"
            )

        if num_threads <= 0:
            raise ValueError(
                "num_threads must be greater than zero"
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero"
            )

        if request_interval_seconds < 0:
            raise ValueError(
                "request_interval_seconds cannot be negative"
            )

        if request_interval_jitter_seconds < 0:
            raise ValueError(
                "request_interval_jitter_seconds cannot be negative"
            )

        if (
            request_interval_jitter_seconds
            > request_interval_seconds
            and request_interval_seconds > 0
        ):
            raise ValueError(
                "request_interval_jitter_seconds cannot exceed "
                "request_interval_seconds"
            )

        self.target_url = target_url.strip()

        self.num_threads = int(
            num_threads
        )

        self.timeout_seconds = float(
            timeout_seconds
        )

        self.request_interval_seconds = float(
            request_interval_seconds
        )

        self.request_interval_jitter_seconds = float(
            request_interval_jitter_seconds
        )

        self.random_seed = int(
            random_seed
        )

        self.event_queue: Queue = (
            event_queue
            if event_queue is not None
            else Queue()
        )

        self._stop_event = Event()

        self._counter_lock = Lock()

        self._threads: list[Thread] = []

        self._session_id: str | None = None
        self._session_start: float | None = None
        self._session_end: float | None = None

        self._requests_sent = 0
        self._success_count = 0
        self._rate_limited_count = 0
        self._failed_count = 0

        self._total_response_time = 0.0
        self._response_samples = 0

    # =========================================================================
    # STATUS
    # =========================================================================

    @property
    def is_running(self) -> bool:
        """
        Return True when at least one worker is alive.
        """

        return any(
            thread.is_alive()
            for thread in self._threads
        )

    @property
    def session_id(self) -> str | None:
        """
        Return the current simulation session identifier.
        """

        return self._session_id

    # =========================================================================
    # START
    # =========================================================================

    def start(
        self,
        *,
        clear_pending_events: bool = True,
    ) -> None:
        """
        Start a fresh simulation session.

        By default, stale events from a previous run are removed from
        the queue before the new session begins.
        """

        if self.is_running:
            raise RuntimeError(
                "Simulation is already running"
            )

        if clear_pending_events:
            self.drain_events()

        self._stop_event.clear()

        self._threads.clear()

        # Create a unique session.
        self._session_id = (
            uuid.uuid4().hex[:12]
        )

        self._session_start = monotonic()
        self._session_end = None

        # Reset counters.
        with self._counter_lock:

            self._requests_sent = 0
            self._success_count = 0
            self._rate_limited_count = 0
            self._failed_count = 0

            self._total_response_time = 0.0
            self._response_samples = 0

        self.event_queue.put(
            {
                "type": "simulation_started",
                "session_id": self._session_id,
                "timestamp": self._session_start,
                "elapsed_seconds": 0.0,
                "target": self.target_url,
                "threads": self.num_threads,
                "request_interval_seconds": (
                    self.request_interval_seconds
                ),
                "request_interval_jitter_seconds": (
                    self.request_interval_jitter_seconds
                ),
            }
        )

        for worker_index in range(
            self.num_threads
        ):

            worker = Thread(
                target=self._worker,
                args=(worker_index,),
                name=f"sim-worker-{worker_index + 1}",
                daemon=True,
            )

            self._threads.append(worker)

            worker.start()

    # =========================================================================
    # STOP
    # =========================================================================

    def stop(self) -> None:
        """
        Stop all workers using one overall shutdown deadline.

        This prevents shutdown time from accumulating worker-by-worker.
        """

        if not self._threads:
            return

        self._stop_event.set()

        shutdown_deadline = (
            monotonic()
            + self.timeout_seconds
            + 1.0
        )

        for worker in self._threads:

            remaining = (
                shutdown_deadline
                - monotonic()
            )

            if remaining <= 0:
                break

            worker.join(
                timeout=remaining
            )

        self._session_end = monotonic()

        elapsed = (
            self._session_end
            - self._session_start
            if self._session_start is not None
            else 0.0
        )

        self.event_queue.put(
            {
                "type": "simulation_stopped",
                "session_id": self._session_id,
                "timestamp": self._session_end,
                "elapsed_seconds": elapsed,
            }
        )

    # =========================================================================
    # SNAPSHOT
    # =========================================================================

    def snapshot(self) -> SimulationSnapshot:
        """
        Return a thread-safe snapshot.
        """

        with self._counter_lock:

            if self._response_samples:

                average_response_ms = (
                    self._total_response_time
                    / self._response_samples
                    * 1000.0
                )

            else:

                average_response_ms = 0.0

            if self._session_start is not None:

                session_end = (
                    self._session_end
                    if self._session_end is not None
                    else monotonic()
                )

                elapsed_seconds = max(
                    0.0,
                    session_end
                    - self._session_start,
                )

            else:

                elapsed_seconds = 0.0

            return SimulationSnapshot(
                requests_sent=self._requests_sent,
                success_count=self._success_count,
                rate_limited_count=(
                    self._rate_limited_count
                ),
                failed_count=self._failed_count,
                average_response_ms=(
                    average_response_ms
                ),
                elapsed_seconds=(
                    elapsed_seconds
                ),
            )

    # =========================================================================
    # EVENT QUEUE
    # =========================================================================

    def drain_events(self) -> list[dict]:
        """
        Remove every pending event from the queue.
        """

        events: list[dict] = []

        while True:

            try:
                events.append(
                    self.event_queue.get_nowait()
                )

            except Empty:
                break

        return events

    # =========================================================================
    # WORKER
    # =========================================================================

    def _worker(
        self,
        worker_index: int,
    ) -> None:
        """
        Execute requests for one logical simulated client.
        """

        session = requests.Session()

        client_id = (
            f"sim-worker-{worker_index + 1}"
        )

        headers = {
            "X-Aegis-Simulated-Client": client_id,
        }

        rng = random.Random(
            self.random_seed + worker_index
        )

        session_id = self._session_id

        try:

            while not self._stop_event.is_set():

                request_start = perf_counter()

                try:

                    response = session.get(
                        self.target_url,
                        headers=headers,
                        timeout=self.timeout_seconds,
                    )

                    elapsed = (
                        perf_counter()
                        - request_start
                    )

                    self._record_response(
                        status_code=(
                            response.status_code
                        ),
                        response_time=elapsed,
                    )

                    session_elapsed = (
                        monotonic()
                        - self._session_start
                        if self._session_start is not None
                        else 0.0
                    )

                    self.event_queue.put(
                        {
                            "type": "request",
                            "session_id": session_id,
                            "timestamp": monotonic(),
                            "elapsed_seconds": (
                                session_elapsed
                            ),
                            "client_id": client_id,
                            "status_code": (
                                response.status_code
                            ),
                            "response_ms": (
                                elapsed * 1000.0
                            ),
                        }
                    )

                except requests.RequestException as exc:

                    elapsed = (
                        perf_counter()
                        - request_start
                    )

                    self._record_failure(
                        response_time=elapsed,
                    )

                    session_elapsed = (
                        monotonic()
                        - self._session_start
                        if self._session_start is not None
                        else 0.0
                    )

                    self.event_queue.put(
                        {
                            "type": "request_error",
                            "session_id": session_id,
                            "timestamp": monotonic(),
                            "elapsed_seconds": (
                                session_elapsed
                            ),
                            "client_id": client_id,
                            "error": str(exc),
                            "response_ms": (
                                elapsed * 1000.0
                            ),
                        }
                    )

                # -------------------------------------------------------------
                # Controlled pacing
                # -------------------------------------------------------------

                if (
                    self.request_interval_seconds > 0
                    and not self._stop_event.is_set()
                ):

                    jitter = 0.0

                    if (
                        self.request_interval_jitter_seconds
                        > 0
                    ):

                        jitter = rng.uniform(
                            -self.request_interval_jitter_seconds,
                            self.request_interval_jitter_seconds,
                        )

                    delay = max(
                        0.0,
                        self.request_interval_seconds
                        + jitter,
                    )

                    self._stop_event.wait(
                        delay
                    )

        finally:

            session.close()

    # =========================================================================
    # RESPONSE RECORDING
    # =========================================================================

    def _record_response(
        self,
        *,
        status_code: int,
        response_time: float,
    ) -> None:
        """
        Record a completed HTTP response safely.
        """

        with self._counter_lock:

            self._requests_sent += 1

            self._total_response_time += (
                response_time
            )

            self._response_samples += 1

            if status_code == 200:

                self._success_count += 1

            elif status_code == 429:

                self._rate_limited_count += 1

            else:

                self._failed_count += 1

    # =========================================================================
    # FAILURE RECORDING
    # =========================================================================

    def _record_failure(
        self,
        *,
        response_time: float,
    ) -> None:
        """
        Record a failed request safely.
        """

        with self._counter_lock:

            self._requests_sent += 1

            self._failed_count += 1

            self._total_response_time += (
                response_time
            )

            self._response_samples += 1