import logging
import functools

from ela.utils import run_function, logger

logging.getLogger(__name__)


def print_result(func):
    @functools.wraps(func)
    async def __inner(*args, **kwargs):
        result = await run_function(func, *args, **kwargs)
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
