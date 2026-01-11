from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable

#Логирование доменных операций
def log_action(action: str, verbose: bool = False) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            logger = logging.getLogger(__name__)
            started = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = int((time.time() - started) * 1000)
                logger.info(
                    "%s result=OK elapsed_ms=%s args=%s kwargs=%s",
                    action,
                    elapsed_ms,
                    args if verbose else "<hidden>",
                    kwargs if verbose else "<hidden>",
                )
                return result
            except Exception as e:
                elapsed_ms = int((time.time() - started) * 1000)
                logger.info(
                    "%s result=ERROR error_type=%s error_message=%s elapsed_ms=%s",
                    action,
                    type(e).__name__,
                    str(e),
                    elapsed_ms,
                )
                raise

        return wrapper

    return decorator