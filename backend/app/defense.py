"""
AegisGuard Adaptive Defense Engine & Dynamic Sliding-Window Rate Limiter
Translates ML risk scores into dynamic defense policies, enforcing temporary restrictions and rate limits.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from time import monotonic
from typing import Deque, Dict, Optional, Tuple


class DefenseLevel(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    current_count: int
    limit: int
    window_seconds: float
    retry_after: float
    action: str


class SlidingWindowRateLimiter:
    def __init__(self, window_seconds: float = 30.0, max_requests: int = 5):
        self.window_seconds = float(window_seconds)
        self.max_requests = int(max_requests)
        self._history: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, client_id: str) -> RateLimitDecision:
        now = monotonic()
        with self._lock:
            history = self._history[client_id]
            cutoff = now - self.window_seconds
            while history and history[0] <= cutoff:
                history.popleft()

            if len(history) >= self.max_requests:
                oldest = history[0]
                retry_after = max(0.5, (oldest + self.window_seconds) - now)
                return RateLimitDecision(
                    allowed=False,
                    current_count=len(history),
                    limit=self.max_requests,
                    window_seconds=self.window_seconds,
                    retry_after=round(retry_after, 2),
                    action="RATE_LIMITED",
                )

            history.append(now)
            return RateLimitDecision(
                allowed=True,
                current_count=len(history),
                limit=self.max_requests,
                window_seconds=self.window_seconds,
                retry_after=0.0,
                action="ALLOWED",
            )

    def reset(self):
        with self._lock:
            self._history.clear()


@dataclass
class _ClientState:
    level: DefenseLevel = DefenseLevel.NORMAL
    risk_score: float = 0.0
    blocked_until: float = 0.0
    last_update: float = 0.0


class AdaptiveDefenseEngine:
    def __init__(
        self,
        normal_threshold: float = 30.0,
        watch_threshold: float = 60.0,
        suspicious_threshold: float = 80.0,
    ):
        self.normal_threshold = normal_threshold
        self.watch_threshold = watch_threshold
        self.suspicious_threshold = suspicious_threshold

        self.limiters = {
            DefenseLevel.NORMAL: SlidingWindowRateLimiter(window_seconds=30, max_requests=5),
            DefenseLevel.WATCH: SlidingWindowRateLimiter(window_seconds=30, max_requests=4),
            DefenseLevel.SUSPICIOUS: SlidingWindowRateLimiter(window_seconds=30, max_requests=2),
            DefenseLevel.HIGH_RISK: SlidingWindowRateLimiter(window_seconds=30, max_requests=1),
        }

        self._clients: Dict[str, _ClientState] = {}
        self._lock = Lock()

    def evaluate(self, client_id: str, risk_score: float) -> Tuple[DefenseLevel, str, bool, int, float]:
        """
        Evaluate client risk and return:
        (defense_level, action, is_blocked, max_requests, restriction_time)
        """
        now = monotonic()
        with self._lock:
            if client_id not in self._clients:
                self._clients[client_id] = _ClientState(last_update=now)

            state = self._clients[client_id]
            state.risk_score = risk_score
            state.last_update = now

            # Auto-expire temporary restrictions
            if state.blocked_until > 0.0 and now >= state.blocked_until:
                state.blocked_until = 0.0

            if risk_score < self.normal_threshold:
                state.level = DefenseLevel.NORMAL
                action = "NORMAL_RATE_LIMIT"
                max_reqs = 5
                block_sec = 0.0
            elif risk_score < self.watch_threshold:
                state.level = DefenseLevel.WATCH
                action = "INCREASED_MONITORING"
                max_reqs = 4
                block_sec = 0.0
            elif risk_score < self.suspicious_threshold:
                state.level = DefenseLevel.SUSPICIOUS
                action = "TEMPORARY_RESTRICTION"
                max_reqs = 2
                block_sec = 10.0
                if state.blocked_until == 0.0:
                    state.blocked_until = now + block_sec
            else:
                state.level = DefenseLevel.HIGH_RISK
                action = "AGGRESSIVE_RATE_LIMIT_ISOLATION"
                max_reqs = 1
                block_sec = 20.0
                if state.blocked_until == 0.0:
                    state.blocked_until = now + block_sec

            is_blocked = (state.blocked_until > now)
            return state.level, action, is_blocked, max_reqs, block_sec

    def check_request(self, client_id: str) -> RateLimitDecision:
        with self._lock:
            state = self._clients.get(client_id)
            level = state.level if state else DefenseLevel.NORMAL
            now = monotonic()
            if state and state.blocked_until > now:
                return RateLimitDecision(
                    allowed=False,
                    current_count=1,
                    limit=1,
                    window_seconds=30.0,
                    retry_after=round(state.blocked_until - now, 2),
                    action="TEMPORARY_RESTRICTION_BLOCKED",
                )

        limiter = self.limiters[level]
        return limiter.check(client_id)

    def reset(self):
        with self._lock:
            self._clients.clear()
            for l in self.limiters.values():
                l.reset()


def calculate_defense_capacity(
    successful_requests: int,
    blocked_requests: int,
    failed_requests: int,
    avg_risk: float,
) -> float:
    """
    Calculate defense capacity percentage:
    defended_traffic = successful_requests + blocked_threat_requests
    Penalizes unexpected server errors or runaway risk.
    """
    total = successful_requests + blocked_requests + failed_requests
    if total == 0:
        return 100.0

    defended = successful_requests + blocked_requests
    base_ratio = (defended / total) * 100.0

    # Slight penalty if system failed to block high risk traffic
    if failed_requests > 0:
        penalty = (failed_requests / total) * 30.0
        base_ratio = max(10.0, base_ratio - penalty)

    return round(float(base_ratio), 1)


adaptive_defense = AdaptiveDefenseEngine()
