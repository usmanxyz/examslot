import threading
import time
from collections.abc import Callable

from fastapi import Request

from app.core.config import Settings
from app.core.errors import RateLimited


class RateLimiter:
    def __init__(self, groups: dict[str, tuple[int, int]]) -> None:
        self._groups = groups
        self._counters: dict[tuple[str, str, float], int] = {}
        self._lock = threading.Lock()

    def check(self, group: str, client: str) -> None:
        limit, window = self._groups[group]
        now = time.monotonic()
        start = now - now % window
        key = (group, client, start)
        with self._lock:
            self._prune(now)
            count = self._counters.get(key, 0) + 1
            self._counters[key] = count
        if count > limit:
            raise RateLimited(max(int(start + window - now) + 1, 1))

    def _prune(self, now: float) -> None:
        stale = [key for key in self._counters if key[2] + self._groups[key[0]][1] <= now]
        for key in stale:
            del self._counters[key]


def build_rate_limiter(settings: Settings) -> RateLimiter:
    return RateLimiter(
        {
            "login": (settings.RATE_LOGIN_LIMIT, settings.RATE_LOGIN_WINDOW_SECONDS),
            "password": (settings.RATE_PASSWORD_LIMIT, settings.RATE_PASSWORD_WINDOW_SECONDS),
            "requests": (settings.RATE_REQUESTS_LIMIT, settings.RATE_REQUESTS_WINDOW_SECONDS),
            "admin_write": (
                settings.RATE_ADMIN_WRITE_LIMIT,
                settings.RATE_ADMIN_WRITE_WINDOW_SECONDS,
            ),
            "api": (settings.RATE_API_LIMIT, settings.RATE_API_WINDOW_SECONDS),
        }
    )


def rate_limit(group: str) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        request.app.state.rate_limiter.check(group, client_ip(request))

    return dependency


def admin_write_limit(request: Request) -> None:
    if request.method != "GET":
        request.app.state.rate_limiter.check("admin_write", client_ip(request))


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
