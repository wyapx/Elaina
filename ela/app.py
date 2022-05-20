import asyncio
import logging
from typing import Dict, Callable

import aiohttp

from . import event
from .api import API
from .message.type import MessageType
from .timer import Timer
from .utils import run_function

logger = logging.getLogger(__name__)


class Mirai(API):
    def __init__(self, baseurl: str, qq: int, verify_key: str, *, loop=None):
        super().__init__(baseurl, qq, verify_key, loop=loop)
        self._route: Dict[str, Callable] = {}

        self._timer = Timer(loop=loop)

    @property
    def timer(self) -> Timer:
        return self._timer

    def register(self, typ: str):
        if typ in self._route:
            raise AttributeError(f"event {typ} already register")

        def __(func):
            if not asyncio.iscoroutinefunction(func) and not callable(func):
                raise ValueError(
                    f"{func.__code__.co_name} is not a callable function"
                )
            self._route[typ] = func

        return __

    @staticmethod
    def _common_handle(inbound_handle, outbound_handle):
        async def inner(data: dict):
            if "code" in data:
                """an error raise"""
                return logger.error(data["code"], data["msg"])
            elif "syncId" in data:
                # a message receive
                data, sync_id = data["data"], data["syncId"]
                if sync_id == "-1":
                    return await inbound_handle(data["type"], data)
                else:
                    return await outbound_handle(data, sync_id)
        return inner

    async def _inbound_message(self, data_type: str, data: dict):
        # qq msg
        if not MessageType.exists(data_type):
            return logger.warning(f'message {data["type"]} not supported, ignore')
        elif data_type not in self._route:
            logger.warning(f"cannot handle {data_type} message, ignore")
        else:
            msg = MessageType.to_message(data_type, data)
            self._timer.executor(
                run_function(self._route[msg.type], self, msg)
            )

    async def _inbound_event(self, data_type: str, data: dict):
        # event
        if data_type in dir(event):
            if data_type in self._route:
                self._timer.executor(
                    run_function(
                        self._route[data_type], self,
                        getattr(event, data_type).parse_obj(data)
                    )
                )
            else:
                logger.warning(f"cannot handle {data_type} event, ignore")
        else:
            logger.warning(f"event {data_type} not found, ignore")

    async def _outbound_receiver(self, data: dict, sync_id: str):
        # result
        if sync_id not in self._msg_future:
            logger.warning(f"syncId {sync_id} not found")
        else:
            self._msg_future.pop(sync_id).set_result(data)

    async def _connect(self) -> bool:
        try:
            self.ws = [
                await self._network.websocket(
                    "/message", self._common_handle(self._inbound_message, self._outbound_receiver)
                ),
                await self._network.websocket(
                    "/event", self._common_handle(self._inbound_event, self._outbound_receiver)
                )
            ]
        except aiohttp.ClientConnectorError:
            logger.exception("Connection Error")
            return False
        return True

    async def close(self):
        await self._network.close()
        await self._network.wait_closed()

    async def async_run(self):
        try:
            if await self._connect():
                logger.info("Application running")
                await self._network.wait_closed()
        finally:
            logger.warning("Application stopped")

    def run(self):
        try:
            self._loop.run_until_complete(
                self._loop.create_task(self.async_run(), name="app")
            )
        except KeyboardInterrupt:
            logger.warning("Interrupt received, stopping...")
            self._loop.run_until_complete(self.close())
