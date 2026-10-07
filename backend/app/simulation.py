"""
AegisGuard Controlled Traffic Simulation Engine
Generates bounded HTTP traffic against authorized laboratory targets, observable in Wireshark.
"""
from __future__ import annotations

import random
import time
import urllib.request
import uuid
from dataclasses import dataclass
from threading import Event, Lock, Thread
from typing import Callable, Dict, List, Optional
import requests

from app.config import (
    LAB_TARGET_URL,
    MAX_ALLOWED_DURATION_SECONDS,
    MAX_ALLOWED_REQUEST_RATE,
    MAX_ALLOWED_WORKERS,
    validate_lab_target,
)
from app.defense import adaptive_defense, calculate_defense_capacity
from app.incidents import incident_manager
from app.ml_detector import ml_detector
from app.redis_layer import redis_manager
from app.telemetry import TelemetryCollector, TelemetryFeatures


@dataclass
class SimulationConfig:
    preset: str = "Controlled Attack"
    workers: int = 6
    request_interval: float = 0.05
    jitter: float = 0.02
    duration: float = 30.0
    target_url: str = LAB_TARGET_URL
    session_id: str = ""


class SimulationEngine:
    def __init__(self, telemetry_collector: TelemetryCollector):
        self.telemetry = telemetry_collector
        self.config = SimulationConfig()
        self.session_id = ""
        self.is_running = False
        self.stop_event = Event()
        self.start_time = 0.0
        self.end_time = 0.0
        
        # Real HTTP response counters
        self.requests_sent = 0
        self.successful_requests = 0
        self.blocked_requests = 0
        self.failed_requests = 0
        self.peak_rate = 0.0
        self.latencies: List[float] = []
        self.risk_scores: List[float] = []
        
        self._threads: List[Thread] = []
        self._monitor_thread: Optional[Thread] = None
        self._lock = Lock()

    def start(self, config: SimulationConfig) -> tuple[bool, str]:
        if self.is_running:
            return False, "Simulation already running."

        # Validate target safety
        is_valid, msg = validate_lab_target(config.target_url)
        if not is_valid:
            return False, msg

        # Bound parameters to lab safety limits
        workers = max(1, min(config.workers, MAX_ALLOWED_WORKERS))
        raw_dur = float(config.duration) if config.duration and config.duration > 0 else 86400.0
        duration = min(raw_dur, MAX_ALLOWED_DURATION_SECONDS)
        interval = max(0.002, float(config.request_interval))
        jitter = max(0.0, float(config.jitter))

        self.config = config
        self.config.workers = workers
        self.config.duration = duration
        self.config.request_interval = interval
        self.config.jitter = jitter
        self.session_id = f"SIM-{int(time.time()*1000)%1000000:06d}"
        self.config.session_id = self.session_id

        # Reset state
        self.stop_event.clear()
        self.requests_sent = 0
        self.successful_requests = 0
        self.blocked_requests = 0
        self.failed_requests = 0
        self.peak_rate = 0.0
        self.latencies.clear()
        self.risk_scores.clear()
        self.telemetry.reset()
        adaptive_defense.reset()
        incident_manager.reset()

        self.start_time = time.time()
        self.is_running = True

        # Publish initial Redis event
        redis_manager.xadd_event(
            "aegisguard:events:stream",
            {
                "timestamp": self.start_time,
                "session_id": self.session_id,
                "type": "SYSTEM",
                "message": f"Simulation initialized with preset '{self.config.preset}' on target {self.config.target_url}",
                "level": "INFO",
            },
        )

        # Spawn worker threads for real HTTP traffic generation
        self._threads = []
        for worker_id in range(workers):
            t = Thread(
                target=self._worker_loop,
                args=(worker_id,),
                daemon=True,
                name=f"TrafficWorker-{worker_id}",
            )
            self._threads.append(t)
            t.start()

        # Start live monitoring / ML pipeline loop
        self._monitor_thread = Thread(
            target=self._telemetry_monitor_loop,
            daemon=True,
            name="TelemetryMLMonitor",
        )
        self._monitor_thread.start()

        return True, self.session_id

    def _worker_loop(self, worker_id: int):
        client_id = f"SIM-CLIENT-{worker_id + 1:03d}"
        from app.search import DEFAULT_CLIENT_IPS
        from app.database import log_request
        client_ip = DEFAULT_CLIENT_IPS.get(client_id, f"192.168.1.{20 + worker_id}")
        session = requests.Session()
        target = self.config.target_url

        while not self.stop_event.is_set():
            # Check duration timeout
            if time.time() - self.start_time >= self.config.duration:
                break

            t0 = time.perf_counter()
            status_code = 0
            size_bytes = 128

            try:
                # Real HTTP request against localhost lab gateway
                resp = session.get(
                    target,
                    headers={
                        "X-Aegis-Simulated-Client": client_id,
                        "X-Aegis-Session": self.session_id,
                        "X-Forwarded-For": client_ip,
                        "User-Agent": "CaptainShield-Lab-Simulator/2.4",
                    },
                    timeout=2.0,
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
                status_code = resp.status_code
                size_bytes = len(resp.content) + len(str(resp.headers))

                with self._lock:
                    self.requests_sent += 1
                    self.latencies.append(latency_ms)
                    if status_code == 200:
                        self.successful_requests += 1
                    elif status_code == 429:
                        self.blocked_requests += 1
                    else:
                        self.failed_requests += 1

            except Exception:
                latency_ms = (time.perf_counter() - t0) * 1000.0
                status_code = 503
                with self._lock:
                    self.requests_sent += 1
                    self.failed_requests += 1

            # Ingest raw observation into telemetry collector
            self.telemetry.record_request(
                client_id=client_id,
                status_code=status_code,
                latency_ms=latency_ms,
                size_bytes=size_bytes,
            )

            # Sample/record to persistent request log
            cur_risk = self.risk_scores[-1] if self.risk_scores else 0.0
            log_request(
                session_id=self.session_id,
                client_id=client_id,
                client_ip=client_ip,
                target_url=target,
                method="GET",
                status_code=status_code,
                latency_ms=latency_ms,
                size_bytes=size_bytes,
                risk_score=cur_risk,
                blocked=(status_code == 429),
            )

            # Controlled pacing with jitter
            base_sleep = self.config.request_interval
            if self.config.jitter > 0:
                sleep_time = max(0.001, base_sleep + random.uniform(-self.config.jitter, self.config.jitter))
            else:
                sleep_time = base_sleep
            time.sleep(sleep_time)

    def _telemetry_monitor_loop(self):
        """Runs every 1 second: telemetry -> Isolation Forest -> adaptive defense -> Redis state."""
        while not self.stop_event.is_set():
            time.sleep(1.0)
            if not self.is_running:
                break

            # 1. Compute 7 features
            feats = self.telemetry.compute_features(session_id=self.session_id)
            vector = feats.as_vector()

            with self._lock:
                self.peak_rate = max(self.peak_rate, feats.request_rate)

            # 2. Run Isolation Forest
            ml_res = ml_detector.predict(vector)
            with self._lock:
                self.risk_scores.append(ml_res.risk_score)

            # 3. Update Adaptive Defense
            def_level, def_action, is_blocked, max_reqs, block_sec = adaptive_defense.evaluate(
                client_id="SIM-GLOBAL",
                risk_score=ml_res.risk_score,
            )

            # 4. Check Incident State
            inc = incident_manager.evaluate(
                session_id=self.session_id,
                risk_score=ml_res.risk_score,
                prediction=ml_res.prediction,
                defense_level=def_level.value,
                action=def_action,
                total_requests=self.requests_sent,
                blocked_requests=self.blocked_requests,
            )

            # 5. Compute Capacity
            with self._lock:
                avg_risk = sum(self.risk_scores) / max(1, len(self.risk_scores))
                capacity = calculate_defense_capacity(
                    self.successful_requests,
                    self.blocked_requests,
                    self.failed_requests,
                    avg_risk,
                )

            # 6. Push to Redis Streams
            telem_payload = {
                **feats.to_dict(),
                "risk_score": ml_res.risk_score,
                "risk_level": ml_res.risk_level,
                "prediction": ml_res.prediction,
                "defense_level": def_level.value,
                "defense_action": def_action,
                "capacity": capacity,
                "successful": self.successful_requests,
                "blocked": self.blocked_requests,
                "failed": self.failed_requests,
            }
            redis_manager.xadd_event("aegisguard:telemetry:stream", telem_payload)
            redis_manager.set_state(f"aegisguard:session:{self.session_id}:state", telem_payload)

            # Emit SOC event logs if state changes or high threat
            if ml_res.prediction == "ANOMALY":
                redis_manager.xadd_event(
                    "aegisguard:events:stream",
                    {
                        "timestamp": time.time(),
                        "session_id": self.session_id,
                        "type": "ML_DETECTOR",
                        "message": f"Anomaly detected by Isolation Forest. Risk: {ml_res.risk_score:.1f}/100. Action: {def_action}",
                        "level": "WARNING" if ml_res.risk_score < 80 else "DANGER",
                    },
                )
            if self.blocked_requests > 0 and self.blocked_requests % 5 == 0:
                redis_manager.xadd_event(
                    "aegisguard:events:stream",
                    {
                        "timestamp": time.time(),
                        "session_id": self.session_id,
                        "type": "RATE_LIMITER",
                        "message": f"HTTP 429 active restriction enforced on {feats.active_clients} clients",
                        "level": "INFO",
                    },
                )

            # Check if duration reached
            if time.time() - self.start_time >= self.config.duration:
                self.stop(reason="Duration completed")

    def stop(self, reason: str = "User stopped") -> Dict:
        with self._lock:
            if not self.is_running:
                return self.get_summary()

            self.stop_event.set()
            self.is_running = False
            self.end_time = time.time()

        # Wait for threads to terminate gracefully
        for t in self._threads:
            t.join(timeout=0.5)

        # Finalize incident
        incident_manager.finalize(self.session_id)

        summary = self.get_summary()
        summary["notes"] = reason
        summary["status"] = "STOPPED" if "stop" in reason.lower() else "COMPLETED"

        # Push termination event
        redis_manager.xadd_event(
            "aegisguard:events:stream",
            {
                "timestamp": self.end_time,
                "session_id": self.session_id,
                "type": "SYSTEM",
                "message": f"Simulation stopped ({reason}). Final requests: {self.requests_sent}, Blocked: {self.blocked_requests}",
                "level": "INFO",
            },
        )

        try:
            from app.database import save_session
            save_session(summary)
        except Exception:
            pass

        return summary

    def get_summary(self) -> Dict:
        duration = max(0.1, (self.end_time or time.time()) - self.start_time)
        avg_lat = sum(self.latencies) / max(1, len(self.latencies))
        avg_risk = sum(self.risk_scores) / max(1, len(self.risk_scores))
        max_risk = max(self.risk_scores) if self.risk_scores else 0.0
        cap = calculate_defense_capacity(
            self.successful_requests,
            self.blocked_requests,
            self.failed_requests,
            avg_risk,
        )

        status = "RUNNING" if self.is_running else ("COMPLETED" if self.requests_sent > 0 else "IDLE")

        return {
            "id": self.session_id,
            "preset": self.config.preset,
            "start_time": self.start_time,
            "end_time": self.end_time or time.time(),
            "duration": round(duration, 1),
            "total_requests": self.requests_sent,
            "successful_requests": self.successful_requests,
            "blocked_requests": self.blocked_requests,
            "failed_requests": self.failed_requests,
            "peak_rate": round(self.peak_rate, 1),
            "avg_latency": round(avg_lat, 2),
            "avg_risk_score": round(avg_risk, 1),
            "max_risk_score": round(max_risk, 1),
            "defense_capacity": cap,
            "incident_count": len(incident_manager.incident_history),
            "status": status,
        }


# Global simulation engine singleton
telemetry_collector = TelemetryCollector()
simulation_engine = SimulationEngine(telemetry_collector)
