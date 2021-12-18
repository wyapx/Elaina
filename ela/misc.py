import asyncio
import functools
import logging

from .utils import run_function

logger = logging.getLogger(__name__)


def print_result(func):
    @functools.wraps(func)
    async def __inner(*args, **kwargs):
        if asyncio.iscoroutinefunction(func):
            result = await run_function(func, *args, **kwargs)
        else:
            result = run_function(func, *args, **kwargs)
        logger.debug(f"{func.__code__.co_name}->({args}, {kwargs})")
        return result

    return __inner


def call_notify(func):
    @functools.wraps(func)
    async def __inner(*args, **kwargs):
        result = await run_function(func, *args, **kwargs)
        logger.debug(f"{func.__code__.co_name} was called")
        return result

    return __inner
