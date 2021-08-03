import asyncio
import logging
from typing import List, Union

from ela.message.base import MessageModel, RemoteResource, UnpreparedResource

logger = logging.getLogger(__name__)


async def run_function(func, *args, **kwargs):
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
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
        chain: List[Union[MessageModel, RemoteResource, UnpreparedResource]]
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
