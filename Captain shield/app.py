from __future__ import annotations

import pickle
from pathlib import Path

from flask import Flask, jsonify, request

from adaptive_defense import (
    AdaptiveDefenseEngine,
    DefenseLevel,
)
from ml_defense_controller import MLDefenseController
from rate_limiter import SlidingWindowRateLimiter


# =============================================================================
# AEGISGUARD LOCAL LAB SERVER
# =============================================================================

app = Flask(__name__)

HOST = "127.0.0.1"
PORT = 5000


# =============================================================================
# RUNTIME ML MODEL
# =============================================================================

MODEL_PATH = Path(__file__).with_name(
    "ml_detector_runtime.pkl"
)


def load_runtime_detector():
    """
    Load the locally saved, fitted ML detector.

    The model file is generated and used only inside the
    AegisGuard controlled local laboratory.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"ML model file not found: {MODEL_PATH}"
        )

    with MODEL_PATH.open("rb") as model_file:
        detector = pickle.load(model_file)

    if not getattr(detector, "is_fitted", False):
        raise RuntimeError(
            "Loaded ML detector is not fitted."
        )

    return detector


ml_detector = load_runtime_detector()


# =============================================================================
# ADAPTIVE DEFENSE
# =============================================================================

adaptive_defense = AdaptiveDefenseEngine(
    normal_threshold=30.0,
    watch_threshold=60.0,
    suspicious_threshold=80.0,
)


ml_defense_controller = MLDefenseController(
    detector=ml_detector,
    defense_engine=adaptive_defense,
)


# =============================================================================
# RATE LIMITERS BY DEFENSE LEVEL
# =============================================================================

rate_limiters = {
    DefenseLevel.NORMAL: SlidingWindowRateLimiter(
        window_seconds=30,
        max_requests=5,
    ),
    DefenseLevel.WATCH: SlidingWindowRateLimiter(
        window_seconds=30,
        max_requests=4,
    ),
    DefenseLevel.SUSPICIOUS: SlidingWindowRateLimiter(
        window_seconds=30,
        max_requests=2,
    ),
    DefenseLevel.HIGH_RISK: SlidingWindowRateLimiter(
        window_seconds=30,
        max_requests=1,
    ),
}


# =============================================================================
# CLIENT IDENTIFICATION
# =============================================================================

def get_client_id() -> str:
    """
    Determine the logical client identity used by the local lab.

    Simulator traffic originating from localhost may provide the
    X-Aegis-Simulated-Client header.

    Ordinary local requests fall back to the localhost address.
    """

    remote_addr = request.remote_addr or "unknown"

    simulated_client = request.headers.get(
        "X-Aegis-Simulated-Client"
    )

    if (
        remote_addr in {"127.0.0.1", "::1"}
        and simulated_client
        and simulated_client.strip()
    ):
        return simulated_client.strip()

    return remote_addr


# =============================================================================
# DEFENSE STATE HELPERS
# =============================================================================

def get_current_defense(client_id: str):
    """
    Return the current adaptive-defense state for a client.

    Unknown clients begin in NORMAL state.
    """

    state = adaptive_defense.get_state(
        client_id
    )

    if state is None:
        return adaptive_defense.evaluate(
            client_id=client_id,
            risk_score=0.0,
        )

    return state


def build_defense_headers(defense) -> dict[str, str]:
    """
    Build response headers exposing the active AegisGuard defense state.
    """

    return {
        "X-Aegis-Defense-Level": defense.level.value,
        "X-Aegis-Risk-Score": f"{defense.risk_score:.2f}",
        "X-Aegis-Defense-Action": defense.action,
    }


# =============================================================================
# MAIN TEST ENDPOINT
# =============================================================================

@app.get("/")
def index():
    """
    Main controlled endpoint used by the simulation engine.

    Request flow:

        Client
          ↓
        Current ML-derived risk state
          ↓
        Adaptive defense
          ↓
        Temporary restriction
          ↓
        Dynamic rate limiter
          ↓
        HTTP response
    """

    client_id = get_client_id()

    # -------------------------------------------------------------------------
    # Obtain current defense state.
    # -------------------------------------------------------------------------

    defense = get_current_defense(
        client_id
    )

    # -------------------------------------------------------------------------
    # Temporary ML-driven restriction.
    # -------------------------------------------------------------------------

    if adaptive_defense.is_blocked(
        client_id
    ):

        # Re-read state after checking the timer so the response
        # reflects the current restriction state.
        current_state = get_current_defense(
            client_id
        )

        response = jsonify(
            {
                "status": "blocked",
                "message": (
                    "Temporary adaptive defense "
                    "restriction active."
                ),
                "client": client_id,
                "risk_score": round(
                    current_state.risk_score,
                    2,
                ),
                "defense_level": (
                    current_state.level.value
                ),
                "defense_action": (
                    "TEMPORARY_RESTRICTION"
                ),
                "limit": (
                    current_state.max_requests
                ),
                "window_seconds": (
                    current_state.window_seconds
                ),
            }
        )

        response.status_code = 429

        response.headers.update(
            build_defense_headers(
                current_state
            )
        )

        response.headers["Retry-After"] = str(
            max(
                1,
                int(
                    current_state.temporary_block_seconds
                ),
            )
        )

        return response

    # -------------------------------------------------------------------------
    # Select the rate limiter according to the ML-driven
    # adaptive defense level.
    # -------------------------------------------------------------------------

    active_limiter = rate_limiters[
        defense.level
    ]

    decision = active_limiter.check(
        client_id
    )

    # -------------------------------------------------------------------------
    # Rate-limited response.
    # -------------------------------------------------------------------------

    if not decision.allowed:

        response = jsonify(
            {
                "status": "rate_limited",
                "message": (
                    "Adaptive rate limit exceeded."
                ),
                "client": client_id,
                "risk_score": round(
                    defense.risk_score,
                    2,
                ),
                "defense_level": (
                    defense.level.value
                ),
                "defense_action": (
                    defense.action
                ),
                "current_count": (
                    decision.current_count
                ),
                "limit": decision.limit,
                "window_seconds": (
                    decision.window_seconds
                ),
                "retry_after": round(
                    decision.retry_after,
                    2,
                ),
            }
        )

        response.status_code = 429

        response.headers.update(
            build_defense_headers(
                defense
            )
        )

        response.headers["Retry-After"] = str(
            max(
                1,
                int(
                    decision.retry_after
                ),
            )
        )

        return response

    # -------------------------------------------------------------------------
    # Accepted response.
    # -------------------------------------------------------------------------

    response = jsonify(
        {
            "status": "ok",
            "message": "Request accepted.",
            "client": client_id,
            "risk_score": round(
                defense.risk_score,
                2,
            ),
            "defense_level": (
                defense.level.value
            ),
            "defense_action": (
                defense.action
            ),
            "current_count": (
                decision.current_count
            ),
            "limit": decision.limit,
            "window_seconds": (
                decision.window_seconds
            ),
        }
    )

    response.status_code = 200

    response.headers.update(
        build_defense_headers(
            defense
        )
    )

    return response


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health")
def health():
    """
    Return service and runtime ML status.
    """

    return jsonify(
        {
            "status": "healthy",
            "service": "AegisGuard Local Lab",
            "adaptive_defense": "enabled",
            "ml_detector": "loaded",
            "ml_model_file": MODEL_PATH.name,
        }
    ), 200


# =============================================================================
# REAL ML INFERENCE → ADAPTIVE DEFENSE
# =============================================================================

@app.post("/lab/ml/analyze")
def analyze_ml_traffic():
    """
    Run the saved ML detector on a seven-feature traffic vector
    and immediately apply the resulting risk score to adaptive defense.

    Expected JSON:

        {
            "client": "SIM-ML-001",
            "features": [
                11.0,
                0.095,
                1.22,
                0.01,
                0.005,
                118.0,
                3.0
            ]
        }

    Feature order:

        1. requests_per_second
        2. average_inter_request_time
        3. burst_ratio
        4. rate_limit_ratio
        5. error_ratio
        6. average_response_time_ms
        7. active_clients
    """

    remote_addr = request.remote_addr or ""

    if remote_addr not in {
        "127.0.0.1",
        "::1",
    }:
        return jsonify(
            {
                "status": "forbidden",
                "message": "Local lab endpoint only.",
            }
        ), 403

    payload = request.get_json(
        silent=True
    )

    if not isinstance(
        payload,
        dict,
    ):
        return jsonify(
            {
                "status": "error",
                "message": (
                    "JSON request body required."
                ),
            }
        ), 400

    client_id = payload.get(
        "client"
    )

    if (
        not isinstance(
            client_id,
            str,
        )
        or not client_id.strip()
    ):
        return jsonify(
            {
                "status": "error",
                "message": (
                    "A non-empty 'client' "
                    "field is required."
                ),
            }
        ), 400

    features = payload.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        return jsonify(
            {
                "status": "error",
                "message": (
                    "'features' must be a list "
                    "of seven numeric values."
                ),
            }
        ), 400

    if len(features) != 7:
        return jsonify(
            {
                "status": "error",
                "message": (
                    "Exactly seven traffic "
                    "features are required."
                ),
            }
        ), 400

    try:
        normalized_features = [
            float(value)
            for value in features
        ]
    except (
        TypeError,
        ValueError,
    ):
        return jsonify(
            {
                "status": "error",
                "message": (
                    "All feature values "
                    "must be numeric."
                ),
            }
        ), 400

    try:
        result = (
            ml_defense_controller
            .analyze_and_defend(
                client_id=client_id.strip(),
                feature_vector=normalized_features,
            )
        )

    except Exception as exc:
        return jsonify(
            {
                "status": "error",
                "message": (
                    "ML analysis failed."
                ),
                "detail": str(exc),
            }
        ), 500

    return jsonify(
        {
            "status": "analyzed",
            "client": result.client_id,
            "prediction": result.prediction,
            "risk_score": round(
                result.risk_score,
                2,
            ),
            "risk_level": result.risk_level,
            "defense_level": (
                result.defense_level
            ),
            "defense_action": (
                result.defense_action
            ),
            "blocked": result.blocked,
            "limit": result.max_requests,
            "window_seconds": (
                result.window_seconds
            ),
            "reason": result.reason,
        }
    ), 200


# =============================================================================
# DEFENSE STATUS
# =============================================================================

@app.get("/lab/defense/status")
def defense_status():
    """
    Return the current adaptive-defense state for a local client.

    Example:

        /lab/defense/status?client=SIM-001
    """

    remote_addr = request.remote_addr or ""

    if remote_addr not in {
        "127.0.0.1",
        "::1",
    }:
        return jsonify(
            {
                "status": "forbidden",
                "message": "Local lab endpoint only.",
            }
        ), 403

    client_id = request.args.get(
        "client",
        "",
    ).strip()

    if not client_id:
        return jsonify(
            {
                "status": "error",
                "message": (
                    "Client query parameter "
                    "is required."
                ),
            }
        ), 400

    state = get_current_defense(
        client_id
    )

    return jsonify(
        {
            "status": "ok",
            "client": state.client_id,
            "risk_score": round(
                state.risk_score,
                2,
            ),
            "defense_level": (
                state.level.value
            ),
            "defense_action": (
                state.action
            ),
            "blocked": adaptive_defense.is_blocked(
                client_id
            ),
            "limit": state.max_requests,
            "window_seconds": (
                state.window_seconds
            ),
        }
    ), 200


# =============================================================================
# LOCAL MANUAL RISK BRIDGE
# =============================================================================

@app.post("/lab/defense/risk")
def set_ml_risk():
    """
    Local testing bridge for supplying a risk score manually.

    This endpoint is retained for controlled testing of the
    adaptive defense layer.

    The normal production flow should use /lab/ml/analyze
    so that risk originates from the ML detector.
    """

    remote_addr = request.remote_addr or ""

    if remote_addr not in {
        "127.0.0.1",
        "::1",
    }:
        return jsonify(
            {
                "status": "forbidden",
                "message": "Local lab endpoint only.",
            }
        ), 403

    payload = request.get_json(
        silent=True
    )

    if not isinstance(
        payload,
        dict,
    ):
        return jsonify(
            {
                "status": "error",
                "message": (
                    "JSON request body required."
                ),
            }
        ), 400

    client_id = payload.get(
        "client"
    )

    if (
        not isinstance(
            client_id,
            str,
        )
        or not client_id.strip()
    ):
        return jsonify(
            {
                "status": "error",
                "message": (
                    "A non-empty 'client' "
                    "field is required."
                ),
            }
        ), 400

    if "risk_score" not in payload:
        return jsonify(
            {
                "status": "error",
                "message": (
                    "'risk_score' field is required."
                ),
            }
        ), 400

    try:
        risk_score = float(
            payload["risk_score"]
        )
    except (
        TypeError,
        ValueError,
    ):
        return jsonify(
            {
                "status": "error",
                "message": (
                    "'risk_score' must be numeric."
                ),
            }
        ), 400

    risk_score = max(
        0.0,
        min(
            100.0,
            risk_score,
        ),
    )

    defense = adaptive_defense.evaluate(
        client_id=client_id.strip(),
        risk_score=risk_score,
    )

    return jsonify(
        {
            "status": "updated",
            "client": defense.client_id,
            "risk_score": round(
                defense.risk_score,
                2,
            ),
            "defense_level": (
                defense.level.value
            ),
            "defense_action": (
                defense.action
            ),
            "blocked": defense.blocked,
            "limit": defense.max_requests,
            "window_seconds": (
                defense.window_seconds
            ),
            "temporary_block_seconds": (
                defense.temporary_block_seconds
            ),
            "reason": defense.reason,
        }
    ), 200


# =============================================================================
# LOCAL LAB RESET
# =============================================================================

@app.post("/lab/reset")
def reset_lab():
    """
    Reset all rate-limiter and adaptive-defense state.
    """

    remote_addr = request.remote_addr or ""

    if remote_addr not in {
        "127.0.0.1",
        "::1",
    }:
        return jsonify(
            {
                "status": "forbidden",
                "message": (
                    "Local lab endpoint only."
                ),
            }
        ), 403

    for limiter in rate_limiters.values():
        limiter.reset_all()

    adaptive_defense.reset_all()

    return jsonify(
        {
            "status": "reset",
            "message": (
                "AegisGuard rate-limiter and "
                "adaptive-defense state cleared."
            ),
        }
    ), 200


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("AegisGuard - Local Simulation Server")
    print("=" * 60)
    print(f"Address          : http://{HOST}:{PORT}")
    print("Mode             : LOCAL LAB ONLY")
    print("ML Detector      : LOADED")
    print("Adaptive Defense : ENABLED")
    print()
    print("Defense Policies:")
    print("  NORMAL     : 5 requests / 30 seconds")
    print("  WATCH      : 4 requests / 30 seconds")
    print("  SUSPICIOUS : 2 requests / 30 seconds")
    print("  HIGH_RISK  : temporary restriction")
    print("=" * 60)
    print()

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        threaded=True,
    )