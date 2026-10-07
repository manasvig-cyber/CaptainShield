"""
AegisGuard Redis Event & Telemetry Infrastructure
Implements Redis Streams, Pub/Sub, and live state caching with resilient fallback.
"""
from __future__ import annotations

import json
import os
import time
from collections import deque
from threading import Lock
from typing import Any, Dict, List, Optional
import redis

from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB


class RedisManager:
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT, db: int = REDIS_DB):
        self.host = host
        self.port = port
        self.db = db
        self._client: Optional[redis.Redis] = None
        self._connected = False
        self._lock = Lock()
        
        self._in_memory_streams: Dict[str, deque] = {}
        self._in_memory_kv: Dict[str, str] = {}
        
        # Connect to Redis if configured / available
        if os.getenv("USE_REDIS", "false").lower() in ("true", "1", "yes"):
            self.connect()

    def connect(self) -> bool:
        try:
            client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
                decode_responses=True,
            )
            if client.ping():
                with self._lock:
                    self._client = client
                    self._connected = True
                return True
        except Exception:
            with self._lock:
                self._client = None
                self._connected = False
        return False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> Dict[str, Any]:
        connected = self.is_connected
        return {
            "status": "CONNECTED" if connected else "STANDALONE_FALLBACK",
            "host": self.host,
            "port": self.port,
            "connected": connected,
            "transport": "Redis Streams / PubSub" if connected else "In-Memory Event Bus",
        }

    def xadd_event(self, stream_name: str, event_data: Dict[str, Any], maxlen: int = 2000) -> str:
        """Publish event to Redis Stream (e.g. aegisguard:telemetry:stream)."""
        serialized = {k: json.dumps(v) if isinstance(v, (dict, list, bool)) else str(v) for k, v in event_data.items()}
        
        if self.is_connected and self._client:
            try:
                entry_id = self._client.xadd(stream_name, serialized, maxlen=maxlen, approximate=True)
                # Also publish to PubSub channel for instant socket delivery
                self._client.publish(f"{stream_name}:pubsub", json.dumps(event_data))
                return entry_id
            except Exception:
                self._connected = False

        # Fallback to local memory stream
        with self._lock:
            if stream_name not in self._in_memory_streams:
                self._in_memory_streams[stream_name] = deque(maxlen=maxlen)
            msg_id = f"{int(time.time()*1000)}-0"
            self._in_memory_streams[stream_name].append({"id": msg_id, "data": event_data, "time": time.time()})
            return msg_id

    def xrevrange_events(self, stream_name: str, count: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent events from Redis Stream."""
        if self.is_connected and self._client:
            try:
                raw_entries = self._client.xrevrange(stream_name, count=count)
                entries = []
                for entry_id, fields in raw_entries:
                    parsed = {}
                    for k, v in fields.items():
                        try:
                            parsed[k] = json.loads(v)
                        except Exception:
                            parsed[k] = v
                    entries.append({"id": entry_id, "data": parsed})
                return entries
            except Exception:
                self._connected = False

        # In-memory fallback
        with self._lock:
            stream = self._in_memory_streams.get(stream_name, deque())
            items = list(stream)[-count:]
            items.reverse()
            return items

    def set_state(self, key: str, value: Any, ttl: Optional[int] = None):
        serialized = json.dumps(value)
        if self.is_connected and self._client:
            try:
                self._client.set(key, serialized, ex=ttl)
                return
            except Exception:
                self._connected = False

        with self._lock:
            self._in_memory_kv[key] = serialized

    def get_state(self, key: str) -> Optional[Any]:
        if self.is_connected and self._client:
            try:
                raw = self._client.get(key)
                return json.loads(raw) if raw else None
            except Exception:
                self._connected = False

        with self._lock:
            raw = self._in_memory_kv.get(key)
            return json.loads(raw) if raw else None


# Global Redis manager singleton
redis_manager = RedisManager()
