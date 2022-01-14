import asyncio
import json
import logging
from typing import Callable, Any, Optional
from urllib import parse

import aiohttp

logger = logging.getLogger(__name__)


class Network:
    def __init__(self, url: str, qq: int, verify_key: str, *, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        self.url = url
        self.qq = qq
        self._closed = asyncio.Event()
        self._loop = loop
        self._session = aiohttp.ClientSession(loop=loop)
        self.__verify_key = verify_key
        self.__session_key = None
        self.__running = True
        self.__ws_count = 0

    @property
    def session_key(self) -> Optional[str]:
        return self.__session_key

    def __join_url(self, target: str, params: dict = None, *, with_key=False) -> str:
        if not params:
            params = {}
        if with_key:
            params["sessionKey"] = self.__session_key
        url = parse.urljoin(self.url, target)
        if params:
            url += f"?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return url

    @property
    def closed(self) -> bool:
        return self._closed.is_set()

    async def close(self):
        self.__running = False
        await self._session.close()
        if not self.__session_key:
            self._closed.set()

    async def wait_closed(self):
        await self._closed.wait()

    async def reset(self):
        if not self.closed:
            raise RuntimeError("cannot reset an active connection")
        self._closed.clear()
        self._session = aiohttp.ClientSession(loop=self._loop)
        self.__session_key = None
        self.__running = True

    async def _http_req(self, method: str, url: str, **kwargs):
        async with getattr(self._session, method.lower())(url, **kwargs) as resp:
            if resp.status != 200:
                raise ConnectionError(200, await resp.read())
            return await resp.json()

    async def get(self, target: str, params=None, **kwargs) -> dict:
        return await self._http_req("GET", self.__join_url(target, params, with_key=True), **kwargs)

    async def post(self, target: str, data: Any, params=None, **kwargs) -> dict:
        return await self._http_req("POST", self.__join_url(target, params, with_key=True), data=data, **kwargs)

    async def _websocket_listen(self, ws: aiohttp.ClientWebSocketResponse, callback, name=None):
        connected = False
        ping_count = 0
        while self.__running:
            try:
                msg = await ws.receive(15)
            except asyncio.TimeoutError:
                if ping_count > 5:
                    logger.warning(f"websocket({name}): timeout, stop")
                    await self.close()
                else:
                    await ws.ping()
                    ping_count += 1
                continue
            if msg.type == aiohttp.WSMsgType.TEXT:
                if connected:
                    try:
                        await callback(
                            **json.loads(msg.data)
                        )
                    except:
                        logger.exception(f"({name}): Callback raise an error")
                        logger.debug(msg.data)
                else:
                    pkg = json.loads(msg.data)
                    if not pkg["syncId"]:
                        data = pkg["data"]
                        if data["code"]:
                            raise ConnectionError(data.pop("code"), data)
                        else:
                            self.__session_key = data["session"]
                            logger.debug(f"websocket({name}): connected")
                            connected = True
            elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED):
                logger.debug(f"websocket({name}): closed")
                await self.close()
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.debug(f"websocket({name}): raise an error")
                break
            elif msg.type == aiohttp.WSMsgType.PONG:
                ping_count = 0

    def __done_cb(self, context: asyncio.Task):
        self.__ws_count -= 1
        if self.__ws_count <= 0:
            self._closed.set()

    async def websocket(self, target: str, callback: Callable, *, name=None):
        """:return aiohttp.ClientWebSocketResponse"""
        if not name:
            name = target
        link = self.__join_url(target, {"qq": self.qq, "verifyKey": self.__verify_key}).replace("http", "ws")
        logger.debug("connecting to " + link)
        ws = await self._session.ws_connect(link, autoping=False)
        self._loop.create_task(
            self._websocket_listen(ws, callback, name)
        ).add_done_callback(self.__done_cb)
        return ws
