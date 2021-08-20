import asyncio
import logging
from typing import Dict, Callable

from .api import API
from .event import events
from .message.type import message_type
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
        def __(func):
            if not asyncio.iscoroutinefunction(func) and not callable(func):
                raise ValueError(
                    f"{func.__code__.co_name} is not a callable function"
                )
            elif typ in self._route:
                raise AttributeError(f"event {typ} already register")
            self._route[typ] = func
        return __

    async def _handle_msg(self, **kwargs):
        if "code" in kwargs:
            """an error raise"""
            return logger.debug(kwargs["code"], kwargs["msg"])
        elif "syncId" in kwargs:
            # a message receive
            data, sync_id = kwargs["data"], kwargs["syncId"]
            if sync_id == "-1":
                # qq msg
                if data["type"] not in message_type:
                    return logger.warning("message %s not supported, ignore" % data["type"])
                msg = message_type[data["type"]](**data)
                if msg.type not in self._route:
                    logger.warning(f"cannot handle {msg.type} message, ignore")
                else:
                    self._timer.executor(
                        run_function(self._route[msg.type], self, msg)
                    )
            else:
                # result
                if sync_id not in self._msg_future:
                    logger.warning(
                        "syncId %s not found" % sync_id
                    )
                else:
                    self._msg_future.pop(sync_id).set_result(data)

    async def _handle_ev(self, **kwargs):
        if "code" in kwargs:
            """an error raise"""
            return logger.debug(kwargs["code"], kwargs["msg"])
        elif "syncId" in kwargs:
            # a message receive
            data, sync_id = kwargs["data"], kwargs["syncId"]
            if sync_id != -1:
                # event
                if data["type"] in dir(events):
                    if data["type"] in self._route:
                        self._timer.executor(
                            run_function(
                                self._route[data["type"]],
                                self,
                                getattr(events, data["type"]).parse_obj(data)
                            )
                        )
                    else:
                        logger.warning(f"cannot handle {data['type']} event, ignore")
                else:
                    logger.warning(f"event {data['type']} not found, ignore")
            else:
                # result
                if sync_id not in self._msg_future:
                    logger.warning(
                        "syncId %s not found" % sync_id
                    )
                else:
                    self._msg_future.pop(sync_id).set_result(data)

    async def _run(self):
        self.ws = [
            await self._network.websocket("/message", self._handle_msg),
            await self._network.websocket("/event", self._handle_ev)
        ]

    def run(self):
        self._loop.run_until_complete(self._run())
        logger.info("Application running")
        try:
            self._loop.run_until_complete(self._network.wait_closed())
        except KeyboardInterrupt:
            logger.warning("Interrupt received, stopping...")
            self._loop.run_until_complete(self._network.close())
            self._loop.close()
        finally:
            logger.warning("Application Stopped")