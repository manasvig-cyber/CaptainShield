"""
AegisGuard - Adaptive ML-Driven Defense Engine

This module converts ML anomaly risk into a dynamic defense state.

Controlled local-lab use only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import Lock
from time import monotonic
from typing import Optional


class DefenseLevel(str, Enum):
    """
    Ordered defense states used by AegisGuard.
    """

    NORMAL = "NORMAL"
    WATCH = "WATCH"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"


@dataclass(frozen=True)
class DefensePolicy:
    """
    Policy applied to a client at a particular defense level.
    """

    level: DefenseLevel
    max_requests: int
    window_seconds: float
    temporary_block_seconds: float
    description: str


@dataclass(frozen=True)
class DefenseDecision:
    """
    Result of evaluating one ML risk score.
    """

    client_id: str
    risk_score: float
    level: DefenseLevel
    action: str
    max_requests: int
    window_seconds: float
    temporary_block_seconds: float
    blocked: bool
    reason: str


@dataclass
class _ClientDefenseState:
    """
    Internal state maintained independently for each client.
    """

    level: DefenseLevel = DefenseLevel.NORMAL
    risk_score: float = 0.0
    blocked_until: float = 0.0
    last_update: float = 0.0


class AdaptiveDefenseEngine:
    """
    ML-driven adaptive defense controller.

    The engine:
    1. receives an ML risk score,
    2. maps it to a defense level,
    3. assigns a rate-limit policy,
    4. optionally activates a temporary restriction,
    5. automatically releases the restriction after its timeout.

    This is a local simulation/lab defense component.
    """

    def __init__(
        self,
        normal_threshold: float = 30.0,
        watch_threshold: float = 60.0,
        suspicious_threshold: float = 80.0,
    ) -> None:
        if not (
            0.0 <= normal_threshold < watch_threshold < suspicious_threshold <= 100.0
        ):
            raise ValueError(
                "Thresholds must satisfy: "
                "0 <= normal_threshold < watch_threshold "
                "< suspicious_threshold <= 100."
            )

        self.normal_threshold = float(normal_threshold)
        self.watch_threshold = float(watch_threshold)
        self.suspicious_threshold = float(suspicious_threshold)

        self._policies = {
            DefenseLevel.NORMAL: DefensePolicy(
                level=DefenseLevel.NORMAL,
                max_requests=5,
                window_seconds=30.0,
                temporary_block_seconds=0.0,
                description="Normal traffic policy",
            ),
            DefenseLevel.WATCH: DefensePolicy(
                level=DefenseLevel.WATCH,
                max_requests=4,
                window_seconds=30.0,
                temporary_block_seconds=0.0,
                description="Increased monitoring and slightly stricter limiting",
            ),
            DefenseLevel.SUSPICIOUS: DefensePolicy(
                level=DefenseLevel.SUSPICIOUS,
                max_requests=2,
                window_seconds=30.0,
                temporary_block_seconds=10.0,
                description="Strict limiting with temporary restriction capability",
            ),
            DefenseLevel.HIGH_RISK: DefensePolicy(
                level=DefenseLevel.HIGH_RISK,
                max_requests=1,
                window_seconds=30.0,
                temporary_block_seconds=20.0,
                description="High-risk traffic temporary restriction",
            ),
        }

        self._clients: dict[str, _ClientDefenseState] = {}
        self._lock = Lock()

    def _get_or_create_client(self, client_id: str) -> _ClientDefenseState:
        """
        Return the internal state for a client.
        """
        state = self._clients.get(client_id)

        if state is None:
            state = _ClientDefenseState(last_update=monotonic())
            self._clients[client_id] = state

        return state

    def _classify_risk(self, risk_score: float) -> DefenseLevel:
        """
        Convert a 0-100 ML risk score into a defense level.
        """
        if risk_score < self.normal_threshold:
            return DefenseLevel.NORMAL

        if risk_score < self.watch_threshold:
            return DefenseLevel.WATCH

        if risk_score < self.suspicious_threshold:
            return DefenseLevel.SUSPICIOUS

        return DefenseLevel.HIGH_RISK

    def evaluate(
        self,
        client_id: str,
        risk_score: float,
    ) -> DefenseDecision:
        """
        Evaluate current ML risk for a client.

        Parameters
        ----------
        client_id:
            Logical client identifier.
        risk_score:
            ML risk score expected in the range 0-100.

        Returns
        -------
        DefenseDecision
            Current defense state and policy.
        """
        if not client_id or not client_id.strip():
            raise ValueError("client_id must not be empty.")

        normalized_client_id = client_id.strip()
        normalized_risk = max(0.0, min(100.0, float(risk_score)))
        now = monotonic()

        with self._lock:
            state = self._get_or_create_client(normalized_client_id)

            # Automatically release an expired temporary restriction.
            if state.blocked_until > 0.0 and now >= state.blocked_until:
                state.blocked_until = 0.0

                if state.level in (
                    DefenseLevel.SUSPICIOUS,
                    DefenseLevel.HIGH_RISK,
                ):
                    state.level = DefenseLevel.WATCH

            new_level = self._classify_risk(normalized_risk)
            policy = self._policies[new_level]

            previous_level = state.level

            state.level = new_level
            state.risk_score = normalized_risk
            state.last_update = now

            # High-risk traffic activates a temporary restriction.
            if new_level == DefenseLevel.HIGH_RISK:
                state.blocked_until = max(
                    state.blocked_until,
                    now + policy.temporary_block_seconds,
                )

                action = "TEMPORARY_RESTRICTION"
                blocked = True

                reason = (
                    f"ML risk score {normalized_risk:.2f} reached HIGH_RISK. "
                    f"Temporary restriction activated for "
                    f"{policy.temporary_block_seconds:.0f} seconds."
                )

            elif new_level == DefenseLevel.SUSPICIOUS:
                # Suspicious traffic gets stricter limiting, but is not fully blocked.
                state.blocked_until = 0.0

                action = "STRICT_RATE_LIMIT"
                blocked = False

                reason = (
                    f"ML risk score {normalized_risk:.2f} classified as "
                    f"SUSPICIOUS. Strict rate limiting applied."
                )

            elif new_level == DefenseLevel.WATCH:
                state.blocked_until = 0.0

                action = "INCREASED_MONITORING"
                blocked = False

                reason = (
                    f"ML risk score {normalized_risk:.2f} classified as WATCH. "
                    f"Increased monitoring and moderate rate limiting applied."
                )

            else:
                state.blocked_until = 0.0

                action = "NORMAL_RATE_LIMIT"
                blocked = False

                reason = (
                    f"ML risk score {normalized_risk:.2f} classified as NORMAL. "
                    f"Normal rate limiting applied."
                )

            # Make recovery visible in the returned action.
            if previous_level != new_level:
                if (
                    previous_level in (
                        DefenseLevel.SUSPICIOUS,
                        DefenseLevel.HIGH_RISK,
                    )
                    and new_level in (
                        DefenseLevel.NORMAL,
                        DefenseLevel.WATCH,
                    )
                ):
                    action = "DEFENSE_RECOVERY"

                    reason = (
                        f"Client recovered from {previous_level.value} to "
                        f"{new_level.value}. Normalized ML risk score: "
                        f"{normalized_risk:.2f}."
                    )

            return DefenseDecision(
                client_id=normalized_client_id,
                risk_score=normalized_risk,
                level=new_level,
                action=action,
                max_requests=policy.max_requests,
                window_seconds=policy.window_seconds,
                temporary_block_seconds=policy.temporary_block_seconds,
                blocked=blocked,
                reason=reason,
            )

    def is_blocked(self, client_id: str) -> bool:
        """
        Check whether a client is currently under temporary restriction.
        """
        if not client_id or not client_id.strip():
            return False

        now = monotonic()

        with self._lock:
            state = self._clients.get(client_id.strip())

            if state is None:
                return False

            if state.blocked_until <= 0.0:
                return False

            if now >= state.blocked_until:
                state.blocked_until = 0.0

                if state.level in (
                    DefenseLevel.SUSPICIOUS,
                    DefenseLevel.HIGH_RISK,
                ):
                    state.level = DefenseLevel.WATCH

                return False

            return True

    def get_state(
        self,
        client_id: str,
    ) -> Optional[DefenseDecision]:
        """
        Return the latest defense state for a client.
        """
        if not client_id or not client_id.strip():
            return None

        normalized_client_id = client_id.strip()

        with self._lock:
            state = self._clients.get(normalized_client_id)

            if state is None:
                return None

            now = monotonic()

            if state.blocked_until > 0.0 and now >= state.blocked_until:
                state.blocked_until = 0.0

            policy = self._policies[state.level]

            blocked = state.blocked_until > now

            return DefenseDecision(
                client_id=normalized_client_id,
                risk_score=state.risk_score,
                level=state.level,
                action=(
                    "TEMPORARY_RESTRICTION"
                    if blocked
                    else "ACTIVE_POLICY"
                ),
                max_requests=policy.max_requests,
                window_seconds=policy.window_seconds,
                temporary_block_seconds=policy.temporary_block_seconds,
                blocked=blocked,
                reason=policy.description,
            )

    def reset_client(self, client_id: str) -> bool:
        """
        Remove one client's adaptive-defense state.
        """
        if not client_id or not client_id.strip():
            return False

        normalized_client_id = client_id.strip()

        with self._lock:
            return self._clients.pop(normalized_client_id, None) is not None

    def reset_all(self) -> None:
        """
        Reset all adaptive-defense state.
        """
        with self._lock:
            self._clients.clear()

    @property
    def client_count(self) -> int:
        """
        Number of clients currently tracked.
        """
        with self._lock:
            return len(self._clients)

    def get_policies(self) -> dict[DefenseLevel, DefensePolicy]:
        """
        Return a copy of all defense policies.
        """
        return dict(self._policies)