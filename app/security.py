from datetime import datetime, timedelta, timezone
from threading import Lock


class LoginAttemptLimiter:
    """Simple in-memory login limiter keyed by user+source."""

    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window = timedelta(seconds=window_seconds)
        self._attempts: dict[str, list[datetime]] = {}
        self._lock = Lock()

    def _prune(self, key: str, now: datetime):
        attempts = self._attempts.get(key, [])
        attempts = [ts for ts in attempts if now - ts <= self.window]
        if attempts:
            self._attempts[key] = attempts
        elif key in self._attempts:
            del self._attempts[key]

    def is_blocked(self, key: str) -> bool:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._prune(key, now)
            return len(self._attempts.get(key, [])) >= self.max_attempts

    def register_failure(self, key: str):
        now = datetime.now(timezone.utc)
        with self._lock:
            self._prune(key, now)
            self._attempts.setdefault(key, []).append(now)

    def clear(self, key: str):
        with self._lock:
            self._attempts.pop(key, None)
