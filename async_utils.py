import asyncio
import aiohttp
import logging
import random
from functools import wraps

logger = logging.getLogger("AI_Assistant.AsyncRetry")

def async_retry(
    retries: int = 3,
    backoff: int = 2,
    exceptions=(aiohttp.ClientError, asyncio.TimeoutError, Exception),
    jitter: bool = True,
):
    """
    Async retry decorator with exponential backoff + optional jitter.
    
    Args:
        retries (int): Max number of attempts.
        backoff (int): Base backoff multiplier.
        exceptions (tuple): Exceptions to catch & retry on.
        jitter (bool): Add randomness to avoid retry storms.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == retries:
                        logger.error("❌ %s failed after %d retries: %s", func.__name__, retries, e)
                        raise
                    
                    # Exponential backoff + jitter
                    sleep_time = (backoff ** attempt)
                    if jitter:
                        sleep_time += random.uniform(0, 1)
                    
                    logger.warning(
                        "⚠️ %s attempt %d/%d failed (%s). Retrying in %.2fs...",
                        func.__name__, attempt, retries, type(e).__name__, sleep_time
                    )
                    await asyncio.sleep(sleep_time)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            return None
        return wrapper
    return decorator