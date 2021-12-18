from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional, Type, BinaryIO
from io import BytesIO

import aiohttp
from pydantic import BaseModel, HttpUrl
from ela.error import ResourceBrokenError


class MessageModelTypes(str, Enum):
    Source = "Source"
    Plain = "Plain"
    Face = "Face"
    At = "At"
    AtAll = "AtAll"
    Image = "Image"
    Quote = "Quote"
    Xml = "Xml"
    Json = "Json"
    App = "App"
    Poke = "Poke"
    FlashImage = "FlashImage"
    Voice = "Voice"
    Forward = "Forward"
    File = "File"
    Dice = "Dice"
    MusicShare = "MusicShare"


class MessageModel(BaseModel):
    type: MessageModelTypes


class RemoteResource(BaseModel):
    url: Optional[HttpUrl]
    path: Optional[Path]
    base64: Optional[str]

    async def get_file_from_url(self) -> bytes:
        async with aiohttp.request("GET", self.url) as resp:
            if resp.status != 200:
                raise ConnectionError(resp.status, await resp.text())
            return await resp.content.readexactly(resp.content_length)

    @classmethod
    @abstractmethod
    def from_path(cls, path: str):
        pass

    @classmethod
    @abstractmethod
    def from_io(cls, obj: BinaryIO):
        pass

    @classmethod
    @abstractmethod
    def from_bytes(cls, data: bytes):
        pass


class Unprepared:
    @abstractmethod
    async def prepare(self, network, utype):
        """
        :type network: ela.network.Network
        :type utype: str
        """


class UnpreparedResource(Unprepared):
    __slots__ = ["resource", "action", "_kwargs"]

    def __init__(self, resource: Type[RemoteResource], action: str, check_resource=True, **kwargs):
        self.resource = resource
        self.action = getattr(self, action)
        self._kwargs = kwargs
        self._check_resource = check_resource

    @staticmethod
    def _check_state(data: dict):
        if "code" not in data:
            return data
        raise ConnectionError(data["code"], data["msg"])

    @staticmethod
    async def upload(network, action: str, utype: str, io: BinaryIO, file_type: str, **extra_field) -> dict:
        form = aiohttp.FormData()
        form.add_field("sessionKey", network.session_key)
        form.add_field("type", utype)
        for k, v in extra_field.items():
            form.add_field(k, v)
        io.seek(0)
        form.add_field(file_type, BytesIO(io.read()))
        return await network.post(action, data=form)

    async def uploadImage(self, network, io: BinaryIO, utype: str):
        return self._check_state(
            await self.upload(network, "/uploadImage", utype, io, "img")
        )

    async def uploadVoice(self, network, io: BinaryIO, utype: str):
        return self._check_state(
            await self.upload(network, "/uploadVoice", utype, io, "voice")
        )

    async def prepare(self, network, utype):
        ret = self.resource(
            **(await self.action(network, utype=utype, **self._kwargs))
        )
        if self._check_resource:
            async with aiohttp.request("GET", ret.url) as resp:
                if resp.status == 200 and resp.content_length:
                    return ret
                raise ResourceBrokenError(resp.status, ret.url)

