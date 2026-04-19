import time
from typing import Callable, Iterable, Optional, TypeVar

from .constants import LOCAL_PARSE_RETRY_DELAY_SECONDS, RETRYABLE_ERROR_MARKERS

TValue = TypeVar("TValue")


def is_retryable_error(error_message: Optional[str], markers: Iterable[str] = None) -> bool:
    if not error_message:
        return False

    marker_set = tuple(markers) if markers else RETRYABLE_ERROR_MARKERS
    lowered = str(error_message).lower()
    return any(marker in lowered for marker in marker_set)


def run_with_retries(
    operation: Callable[[], TValue],
    *,
    max_retries: int,
    delay_seconds: float = LOCAL_PARSE_RETRY_DELAY_SECONDS,
    retryable_checker: Callable[[Exception], bool] = None,
) -> TValue:
    if max_retries < 1:
        raise ValueError("max_retries must be >= 1")

    checker = retryable_checker or (lambda _: True)
    current_delay = max(0.0, delay_seconds)
    last_exception: Exception = RuntimeError("run_with_retries failed before first attempt")

    for attempt in range(1, max_retries + 1):
        try:
            return operation()
        except Exception as exc:
            last_exception = exc
            can_retry = attempt < max_retries and checker(exc)
            if not can_retry:
                raise
            if current_delay > 0:
                time.sleep(current_delay)
                current_delay = min(current_delay * 2, 2.0)

    raise last_exception
