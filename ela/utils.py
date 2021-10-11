import logging
import asyncio
import functools
from typing import List, Union

from .message.base import MessageModel, RemoteResource, UnpreparedResource
from .types import T

logger = logging.getLogger(__name__)
_LOOP = asyncio.get_event_loop()


async def run_function(func, *args, **kwargs):
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    elif asyncio.iscoroutine(func):
        return func
    else:
        return func(*args, **kwargs)


def assert_success(data: dict, return_obj=None):
    if "code" not in data:
        if not data:
            raise ValueError("empty element")
    elif data["code"] != 0:
        raise ConnectionError(data["code"], data["msg"])
    if return_obj:
        return data.get(return_obj)
    else:
        return data


async def prepare_chain(
        network,
        utype: str,
        chain: T.Chain
) -> List[Union[MessageModel, RemoteResource]]:
    if isinstance(chain, list):
        new_chain: List[Union[MessageModel, RemoteResource]] = []
        for item in chain:
            if isinstance(item, UnpreparedResource):
                new_chain.append(await item.prepare(network, utype))
            else:
                new_chain.append(item)
        return new_chain
    else:
        raise TypeError("expect list chain, but %s got" % type(chain))


def call_later(delay: int, func, *args, **kwargs) -> asyncio.TimerHandle:
    logger.debug(f"function {func} will execute in {delay}s")
    return _LOOP.call_later(delay, run_function(func, *args, **kwargs))
