from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Deque


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """
    Result returned by the rate limiter for a single request.
    """

    allowed: bool
    current_count: int
    limit: int
    window_seconds: float
    retry_after: float


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding-window rate limiter.

    Default configuration mirrors the supplied project screenshot:

        TIME_WINDOW = 30 seconds
        MAX_REQUESTS = 5 requests per window

    The first five requests inside the active window are allowed.
    Subsequent requests are rate-limited until an old request
    expires from the window.
    """

    def __init__(
        self,
        *,
        window_seconds: float = 30.0,
        max_requests: int = 5,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError(
                "window_seconds must be greater than 0"
            )

        if max_requests <= 0:
            raise ValueError(
                "max_requests must be greater than 0"
            )

        self.window_seconds = float(window_seconds)
        self.max_requests = int(max_requests)

        # Each client gets its own request timestamp queue.
        self._history: dict[str, Deque[float]] = defaultdict(deque)

        # The simulator will eventually use multiple threads,
        # so shared rate-limit state must be protected.
        self._lock = Lock()

    def check(self, client_id: str) -> RateLimitDecision:
        """
        Register a request and determine whether it is allowed.

        Parameters
        ----------
        client_id:
            Identifier of the requesting client.

        Returns
        -------
        RateLimitDecision
            Structured result describing the decision.
        """

        if not client_id:
            raise ValueError("client_id cannot be empty")

        now = monotonic()

        with self._lock:
            history = self._history[client_id]

            # Remove timestamps that are outside the active window.
            self._prune(history, now)

            # If the client already reached the limit,
            # do not add another timestamp.
            if len(history) >= self.max_requests:
                retry_after = self._calculate_retry_after(
                    history,
                    now,
                )

                return RateLimitDecision(
                    allowed=False,
                    current_count=len(history),
                    limit=self.max_requests,
                    window_seconds=self.window_seconds,
                    retry_after=retry_after,
                )

            # Request is allowed, so record it.
            history.append(now)

            return RateLimitDecision(
                allowed=True,
                current_count=len(history),
                limit=self.max_requests,
                window_seconds=self.window_seconds,
                retry_after=0.0,
            )

    def get_client_count(self, client_id: str) -> int:
        """
        Return the number of active requests for a client
        inside the current time window.
        """

        if not client_id:
            return 0

        now = monotonic()

        with self._lock:
            history = self._history.get(client_id)

            if not history:
                return 0

            self._prune(history, now)

            return len(history)

    def reset_client(self, client_id: str) -> None:
        """
        Clear rate-limit state for a single client.
        """

        if not client_id:
            return

        with self._lock:
            self._history.pop(client_id, None)

    def reset_all(self) -> None:
        """
        Clear rate-limit state for every client.
        """

        with self._lock:
            self._history.clear()

    def _prune(
        self,
        history: Deque[float],
        now: float,
    ) -> None:
        """
        Remove timestamps older than the configured window.
        """

        cutoff = now - self.window_seconds

        while history and history[0] <= cutoff:
            history.popleft()

    def _calculate_retry_after(
        self,
        history: Deque[float],
        now: float,
    ) -> float:
        """
        Calculate approximately how many seconds remain
        until the oldest request leaves the active window.
        """

        if not history:
            return 0.0

        remaining = (
            self.window_seconds
            - (now - history[0])
        )

        return max(0.0, remaining)