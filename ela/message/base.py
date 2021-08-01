from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional, Type

import aiohttp
from pydantic import BaseModel, HttpUrl


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
    Unknown = "Unknown"
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

    @staticmethod
    @abstractmethod
    def from_path(path: str):
        pass

    @staticmethod
    @abstractmethod
    def from_io():
        pass


class UnpreparedResource:
    __slots__ = ["resource", "action", "_kwargs"]

    def __init__(self, resource: Type[RemoteResource], action: str, **kwargs):
        self.resource = resource
        self.action = getattr(self, action)
        self._kwargs = kwargs

    @staticmethod
    async def upload(network, target: str, utype: str, file_path: str, file_type: str, **extra_field) -> dict:
        form = aiohttp.FormData()
        form.add_field("sessionKey", network.session_key)
        form.add_field("type", utype)
        form.add_field(file_type, open(file_path, "rb"))
        for k, v in extra_field.items():
            form.add_field(k, v)
        return await network.post(target, data=form)

    async def uploadImage(self, network, path: str, utype: str):
        return await self.upload(network, "/uploadImage", utype, path, "img")

    async def uploadVoice(self, network, path: str, utype: str):
        return await self.upload(network, "/uploadVoice", utype, path, "voice")

    async def uploadFile(self, network, file_path: str, utype: str, path=""):
        return await self.upload(network, "/file/upload", utype, file_path, "file", path=path)

    async def prepare(self, network, utype):
        """
        :type network: mpy.network.Network
        :type utype: str
        """
        data = await self.action(network, utype=utype, **self._kwargs)
        if "code" in data:
            raise ConnectionError(data["code"], data["msg"])
        return self.resource(**data)
