import time
import threading


class RateLimiter:
    """Token-bucket rate limiter for API calls."""

    def __init__(self, max_calls: int = 5, period_seconds: float = 10.0):
        self._max_calls = max_calls
        self._period = period_seconds
        self._calls: list[float] = []
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            self._calls = [t for t in self._calls if now - t < self._period]

            if len(self._calls) >= self._max_calls:
                sleep_time = self._period - (now - self._calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self._calls = [t for t in self._calls if time.monotonic() - t < self._period]

            self._calls.append(time.monotonic())

    def reset(self) -> None:
        with self._lock:
            self._calls.clear()
