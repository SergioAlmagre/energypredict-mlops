from collections import defaultdict, deque
from time import time

from fastapi import HTTPException, status


class LoginFailureGuard:
    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def _purge(self, key: str, window_seconds: int) -> deque[float]:
        now = time()
        threshold = now - window_seconds
        q = self._attempts[key]
        while q and q[0] < threshold:
            q.popleft()
        return q

    def ensure_allowed(self, key: str, max_attempts: int, window_seconds: int) -> None:
        q = self._purge(key, window_seconds)
        if len(q) >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
            )

    def register_failure(self, key: str, window_seconds: int) -> None:
        q = self._purge(key, window_seconds)
        q.append(time())

    def register_success(self, key: str) -> None:
        self._attempts.pop(key, None)


login_failure_guard = LoginFailureGuard()
