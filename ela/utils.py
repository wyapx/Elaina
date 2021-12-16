import asyncio
import logging
from typing import List, Union, Callable, Coroutine

from .message.base import MessageModel, RemoteResource, Unprepared
from .error import ResourceBrokenError

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
    elif return_obj:
        return data.get(return_obj)
    else:
        return data


async def prepare_chain(network, utype: str, chain) -> List[Union[MessageModel, RemoteResource]]:
    if isinstance(chain, list):
        new_chain: List[Union[MessageModel, RemoteResource]] = []
        for item in chain:
            if isinstance(item, Unprepared):
                for c in range(1, 3):
                    try:
                        new_chain.append(await item.prepare(network, utype))
                        break
                    except ResourceBrokenError as e:
                        logger.warning(f"Resource '{e}' broken, retry {c} times now")
                else:
                    logger.error("all attempting failed, give up")
            else:
                new_chain.append(item)
        return new_chain
    else:
        raise TypeError("expect list chain, but %s got" % type(chain))


def call_later(delay: int, func, *args, **kwargs) -> asyncio.TimerHandle:
    logger.debug(f"function {func} will execute in {delay}s")
    return _LOOP.call_later(delay, _LOOP.create_task, run_function(func, *args, **kwargs))


async def async_retry(coro: Callable[[], Coroutine], count: int, *, loop=None) -> bool:
    if not loop:
        loop = asyncio.get_event_loop()
    while count >= 0:
        task = loop.create_task(coro())
        if await task:
            err = task.exception()
            if err:
                logger.exception(f"function {coro} raise an error, {count} times remain")
                count -= 1
            else:
                return True
    return False

