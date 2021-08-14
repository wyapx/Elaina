import json
import logging
import asyncio
from typing import Callable, Any, Optional

import aiohttp
from urllib import parse
from .utils import assert_success

logger = logging.getLogger(__name__)


class Network:
    def __init__(self, url: str, qq: int, verify_key: str, *, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        self.url = url
        self.qq = qq
        self._loop = loop
        self._session = aiohttp.ClientSession(loop=loop)
        self.__verify_key = verify_key
        self.__session_key = None
        self.__stop = False

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

    async def stop(self):
        self.__stop = True
        await self._session.close()

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
        while not self.__stop:
            try:
                msg = await ws.receive(15)
            except asyncio.TimeoutError:
                if ping_count > 5:
                    logger.warning(f"websocket({name}): timeout, stop")
                    await self.stop()
                else:
                    await ws.ping()
                    ping_count += 1
                    # logger.debug(f"websocket({name}): ping")
                continue
            if msg.type == aiohttp.WSMsgType.TEXT:
                if connected:
                    try:
                        await callback(
                            **json.loads(msg.data)
                        )
                    except:
                        logger.exception(f"({name}): Callback raise an error")
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
                await self.stop()
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.debug(f"websocket({name}): raise an error")
                break
            elif msg.type == aiohttp.WSMsgType.PONG:
                # logger.debug(f"websocket({name}): pong")
                ping_count = 0

    async def websocket(self, target: str, callback: Callable, *, name=None):
        """:return aiohttp.ClientWebSocketResponse"""
        if not name:
            name = target
        if self.url.startswith("https"):
            base = self.url.replace("https", "wss")
        else:
            base = self.url.replace("http", "ws")
        link = parse.urljoin(base, target) + f"?verifyKey={self.__verify_key}&qq={self.qq}"
        logger.debug("connecting to " + link)
        ws = await self._session.ws_connect(link, autoping=False)
        self._loop.create_task(
            self._websocket_listen(ws, callback, name)
        )
        return ws


class _HTTP:
    """
    弃用的类
    里面的功能可以正常使用
    """
    def __init__(self, url: str, qq: int, verify_key: str, *, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        self.url = url
        self.qq = qq
        self._loop = loop
        self._session = aiohttp.ClientSession(loop=loop)
        self.__verify_key = verify_key
        self.__session_key = None
        self.__stop = False

    def __join_url(self, target: str, params: dict = None, *, with_key=False) -> str:
        if not params:
            params = {}
        if with_key:
            params["sessionKey"] = self.__session_key
        url = parse.urljoin(self.url, target)
        if params:
            url += f"?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return url

    async def stop(self):
        self.__stop = True
        if self.__session_key:
            await self.release()
        await self._session.close()

    async def _http_req(self, method: str, url: str, **kwargs):
        print(method, url, kwargs)
        async with getattr(self._session, method.lower())(url, **kwargs) as resp:
            print(resp.request_info.headers)
            if resp.status != 200:
                raise ConnectionError(200, await resp.read())
            return await resp.json()

    async def release(self):
        assert_success(
            await self._http_req("POST", self.__join_url("/bind"), json={"sessionKey": self.__session_key, "qq": self.qq})
        )

    async def bind(self):
        session_key = assert_success(
            await self._http_req("POST", self.__join_url("/verify"), json={"verifyKey": self.__verify_key}),
            return_obj="session"
        )
        assert_success(await self._http_req("POST", self.__join_url("/bind"), json={"sessionKey": session_key, "qq": self.qq}))
        print(session_key)
        self.__session_key = session_key
