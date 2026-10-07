"""
AegisGuard 7-Feature Telemetry Pipeline
Ingests raw request observations and computes rolling 7-feature numerical vectors.
"""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from statistics import mean
from threading import Lock
from time import monotonic, time
from typing import Deque, Dict, List, Optional


@dataclass(frozen=True)
class TelemetryFeatures:
    timestamp: float
    session_id: str
    request_rate: float
    request_interval: float
    request_burstiness: float
    response_latency: float
    client_frequency: float
    request_size: float
    error_rate: float
    active_clients: int
    total_requests: int

    def as_vector(self) -> List[float]:
        return [
            round(self.request_rate, 4),
            round(self.request_interval, 6),
            round(self.request_burstiness, 4),
            round(self.response_latency, 2),
            round(self.client_frequency, 4),
            round(self.request_size, 2),
            round(self.error_rate, 4),
        ]

    def to_dict(self) -> Dict[str, float]:
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "request_rate": self.request_rate,
            "request_interval": self.request_interval,
            "request_burstiness": self.request_burstiness,
            "response_latency": self.response_latency,
            "client_frequency": self.client_frequency,
            "request_size": self.request_size,
            "error_rate": self.error_rate,
            "active_clients": self.active_clients,
            "total_requests": self.total_requests,
        }


@dataclass(slots=True)
class _RequestEvent:
    timestamp: float
    status_code: int
    latency_ms: float
    client_id: str
    size_bytes: int


class TelemetryCollector:
    def __init__(self, window_seconds: float = 2.0):
        self.window_seconds = max(0.5, float(window_seconds))
        self._history: Deque[_RequestEvent] = deque()
        self._lock = Lock()
        self._total_requests = 0

    def record_request(
        self,
        client_id: str,
        status_code: int,
        latency_ms: float,
        size_bytes: int = 256,
    ):
        now = monotonic()
        with self._lock:
            self._total_requests += 1
            self._history.append(
                _RequestEvent(
                    timestamp=now,
                    status_code=int(status_code),
                    latency_ms=max(0.1, float(latency_ms)),
                    client_id=client_id or "client-unknown",
                    size_bytes=int(size_bytes),
                )
            )
            # Prune events older than 3 * window
            cutoff = now - (self.window_seconds * 3)
            while self._history and self._history[0].timestamp < cutoff:
                self._history.popleft()

    def compute_features(self, session_id: str = "") -> TelemetryFeatures:
        now = monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            events = [e for e in self._history if e.timestamp >= cutoff]
            total_reqs = self._total_requests

        if not events:
            return TelemetryFeatures(
                timestamp=time(),
                session_id=session_id,
                request_rate=0.0,
                request_interval=0.25,
                request_burstiness=1.0,
                response_latency=2.5,
                client_frequency=0.0,
                request_size=256.0,
                error_rate=0.0,
                active_clients=0,
                total_requests=total_reqs,
            )

        count = len(events)
        rate = count / self.window_seconds
        
        # Inter-request time
        if count > 1:
            timestamps = [e.timestamp for e in events]
            intervals = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:]) if (t2 - t1) >= 0]
            avg_interval = mean(intervals) if intervals else (self.window_seconds / count)
        else:
            avg_interval = self.window_seconds

        # Burstiness: ratio of peak half-second count to average
        half_window = self.window_seconds / 2.0
        first_half = sum(1 for e in events if e.timestamp < (cutoff + half_window))
        second_half = count - first_half
        burstiness = max(first_half, second_half) / max(1.0, count / 2.0)

        # Response latency
        avg_latency = mean(e.latency_ms for e in events)

        # Client diversity / frequency
        client_counts = Counter(e.client_id for e in events)
        active_clients = len(client_counts)
        client_frequency = (client_counts.most_common(1)[0][1] / count) if count > 0 else 0.0

        # Request size
        avg_size = mean(e.size_bytes for e in events)

        # Error / 429 rate
        error_count = sum(1 for e in events if e.status_code == 429 or e.status_code >= 500)
        error_rate = error_count / count

        return TelemetryFeatures(
            timestamp=time(),
            session_id=session_id,
            request_rate=round(rate, 2),
            request_interval=round(avg_interval, 5),
            request_burstiness=round(burstiness, 3),
            response_latency=round(avg_latency, 2),
            client_frequency=round(client_frequency, 3),
            request_size=round(avg_size, 1),
            error_rate=round(error_rate, 4),
            active_clients=active_clients,
            total_requests=total_reqs,
        )

    def reset(self):
        with self._lock:
            self._history.clear()
            self._total_requests = 0
