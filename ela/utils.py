import asyncio
import logging
from typing import List, Union, Callable, Coroutine

import aiohttp

from .message.base import MessageModel, RemoteResource, Unprepared

logger = logging.getLogger(__name__)
_LOOP = asyncio.get_event_loop()


async def run_function(func, *args, **kwargs):
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    elif asyncio.iscoroutine(func):
        return await func
    else:
        return func(*args, **kwargs)


def assert_success(data: dict, return_obj=None):
    if "code" not in data:
        if not data:
            raise ValueError("empty element")
    elif data["code"] != 0:
        raise ConnectionError(data["code"], data["msg"])
    return data.get(return_obj) if return_obj else data


async def prepare_chain(network, utype: str, chain) -> List[Union[MessageModel, RemoteResource]]:
    if not isinstance(chain, list):
        raise TypeError(f"expect list chain, but {type(chain)} got")
    new_chain: List[Union[MessageModel, RemoteResource]] = []
    for item in chain:
        if isinstance(item, Unprepared):
            new_chain.append(await item.prepare(network, utype))
        else:
            new_chain.append(item)
    return new_chain


def call_later(delay: int, func, *args, **kwargs) -> asyncio.TimerHandle:
    logger.debug(f"function {func} will execute in {delay}s")
    return _LOOP.call_later(delay, _LOOP.create_task, run_function(func, *args, **kwargs))


async def async_retry(coro: Callable[[], Coroutine], count: int, *, loop=None) -> bool:
    if not loop:
        loop = asyncio.get_event_loop()
    while count >= 0:
        task = loop.create_task(coro())
        if await task:
            if task.exception():
                logger.exception(f"function {coro} raise an error, {count} times remain")
                count -= 1
            else:
                return True
    return False


async def _run_app(app, close):
    logger.info("Daemon running")
    while not close.is_set():
        logger.debug("Checking availability...")
        try:
            async with aiohttp.request("GET", app.network.url) as resp:
                # todo: connection state support
                pass
        except aiohttp.ClientConnectionError:
            logger.warning("Cannot connect to frontend, retry after 30s")
            await asyncio.sleep(30)
            continue
        logger.debug("Service available")
        await app.async_run()
        if not close.is_set():
            logger.warning("Application exit, restarting")
            await app.network.reset()


def run_app(app):
    close = asyncio.Event()
    daemon = _LOOP.create_task(_run_app(app, close), name="daemon")
    try:
        _LOOP.run_until_complete(daemon)
    except KeyboardInterrupt:
        logger.warning("Interrupt received, stopping...")
        close.set()
        _LOOP.run_until_complete(app.close())
    logger.info("Daemon stopped")
