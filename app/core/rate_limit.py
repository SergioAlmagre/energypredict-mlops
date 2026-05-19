from collections import defaultdict, deque
from collections.abc import Callable
from time import time

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = time()
        queue = self._hits[key]
        threshold = now - window_seconds
        while queue and queue[0] < threshold:
            queue.popleft()
        if len(queue) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )
        queue.append(now)


rate_limiter = InMemoryRateLimiter()


def limit_by_ip(scope: str, limit: int, window_seconds: int) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        key = f"{scope}:{client_host}"
        rate_limiter.check(key=key, limit=limit, window_seconds=window_seconds)

    return dependency
