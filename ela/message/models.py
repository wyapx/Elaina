import os
import random
from enum import Enum
from io import BytesIO
from typing import Optional, Union, Literal, BinaryIO

from .base import MessageModel, RemoteResource, MessageModelTypes, UnpreparedResource
from ..component.group import Member


class Source(MessageModel):
    type = MessageModelTypes.Source
    id: int
    time: int

    def __init__(self, id: int, time: int, **_):
        super(Source, self).__init__(
            id=id,
            time=time
        )

    def __int__(self):
        return self.id

    def __str__(self):
        return f"[source:{self.id}]"


class Plain(MessageModel):
    type = MessageModelTypes.Plain
    text: str

    def __init__(self, text: str, **_):
        super(Plain, self).__init__(text=text)

    def __str__(self):
        return self.text


class At(MessageModel):
    type = MessageModelTypes.At
    target: int
    display: Optional[str]

    def __init__(self, target: Union[int, Member], **_):
        super(At, self).__init__(target=target)

    def __str__(self):
        return f"[mirai:at:{self.target}]"


class AtAll(MessageModel):
    type = MessageModelTypes.AtAll

    def __str__(self):
        return "[mirai:atall]"


class Face(MessageModel):
    type = MessageModelTypes.Face
    faceId: int
    name: str

    def __init__(self, faceId: int, name: str, **_):
        super(Face, self).__init__(
            faceId=faceId,
            name=name
        )

    def __str__(self):
        return f"[mirai:face:{self.faceId}']"


class Image(MessageModel, RemoteResource):
    type = MessageModelTypes.Image
    imageId: Optional[str]

    def __init__(self, imageId=None, path=None, url=None, base64=None, **_):
        """
        :type imageId: str
        :type path: Path
        :type url: HttpUrl
        :type base64: str
        """
        super(Image, self).__init__(
            imageId=imageId,
            path=path,
            url=url,
            base64=base64
        )

    @staticmethod
    def from_path(path: str):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        return UnpreparedResource(Image, "uploadImage", io=open(path, "rb"))

    @staticmethod
    def from_io(obj: BinaryIO):
        return UnpreparedResource(Image, "uploadImage", io=obj)

    @staticmethod
    def from_bytes(data: bytes):
        return Image.from_io(BytesIO(data))

    def __str__(self):
        return f"[mirai:image:{self.imageId}]"


class FlashImage(Image):
    type = MessageModelTypes.FlashImage

    @staticmethod
    def from_path(path: str):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        return UnpreparedResource(FlashImage, "uploadImage", io=open(path, "rb"))

    @staticmethod
    def from_io(obj: BinaryIO):
        return UnpreparedResource(FlashImage, "uploadImage", io=obj)

    @staticmethod
    def from_bytes(data: bytes):
        return FlashImage.from_io(BytesIO(data))

    def __str__(self):
        return f"[mirai:flash:{self.imageId}]"


class Voice(MessageModel, RemoteResource):
    type = MessageModelTypes.Voice
    length: Optional[int]
    voiceId: Optional[str]

    def __init__(self, voiceId=None, path=None, url=None, base64=None, **_):
        """
        :type voiceId: str
        :type path: Path
        :type url: HttpUrl
        :type base64: str
        """
        super(Voice, self).__init__(
            voiceId=voiceId,
            path=path,
            url=url,
            base64=base64
        )

    @staticmethod
    def from_path(path: str):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        return UnpreparedResource(Voice, "uploadVoice", io=open(path, "rb"))

    @staticmethod
    def from_io(obj: BinaryIO):
        return UnpreparedResource(Voice, "uploadVoice", io=obj)

    @staticmethod
    def from_bytes(data: bytes):
        return Voice.from_io(BytesIO(data))

    def __str__(self):
        return f"[mirai:voice:{self.voiceId}]"


class Xml(MessageModel):
    type = MessageModelTypes.Xml
    xml: str

    def __init__(self, xml: str, **_):
        super(Xml, self).__init__(xml=xml)

    def __str__(self):
        return f"[mirai:xml:{self.xml}]"


class Json(MessageModel):
    """
    废弃的方法，请使用App代替
    """

    type = MessageModelTypes.Json
    Json: str

    def __init__(self, json: str, **_):
        super(Json, self).__init__(Json=json)

    def dict(self, *_, **kwargs) -> dict:
        data = dict(
            *self._iter(
                to_dict=True,
                **kwargs
            )
        )
        data["json"] = data.pop("Json")
        return data

    def __str__(self):
        return f"[mirai:json:{self.Json}]"


class App(MessageModel):
    type = MessageModelTypes.App
    content: str

    def __init__(self, content: str, **_):
        super(App, self).__init__(content=content)

    def __str__(self):
        return f"[mirai:app:{self.content}]"


class Poke(MessageModel):
    type = MessageModelTypes.Poke
    name: str

    class Type(Enum):
        SixSixSix = ("SixSixSix", 5, -1)
        ShowLove = ("ShowLove", 2, -1)
        Like = ("Like", 3, -1)
        Heartbroken = ("Heartbroken", 4, -1)
        FangDaZhao = ("FangDaZhao", 6, -1)
        ChuoYiChuo = ("ChuoYiChuo", 1, -1)

    @classmethod
    def random_type(cls):
        return cls(
            random.choice(
                (
                    cls.Type.SixSixSix,
                    cls.Type.ShowLove,
                    cls.Type.ChuoYiChuo,
                    cls.Type.Like,
                    cls.Type.FangDaZhao,
                    cls.Type.Heartbroken
                )
            )
        )

    def __init__(self, name: Type, **_):
        if isinstance(name, self.Type):
            super(Poke, self).__init__(name=name.value[0])
        else:
            super(Poke, self).__init__(name=name)

    def __str__(self):
        # mapper: https://github.com/mamoe/mirai/blob/dev/mirai-core-api/src/commonMain/kotlin/message/data/PokeMessage.kt#L60
        return "[mirai:poke:{0},{1},{2}]".format(*getattr(self.Type, self.name).value)


class Dice(MessageModel):
    type = MessageModelTypes.Dice
    value: int

    def __init__(self, value: Literal[1, 2, 3, 4, 5, 6], **_):
        if not 1 <= value <= 6:
            raise OverflowError(
                f"value must be in 1 to 6, {value} got"
            )
        super(Dice, self).__init__(value=value)

    def __int__(self):
        return self.value

    def __str__(self):
        return f"[mirai:dice:{self.value}]"


class MusicShare(MessageModel):
    type = MessageModelTypes.MusicShare
    kind: str
    title: str
    summary: str
    jumpUrl: str
    pictureUrl: str
    musicUrl: str
    brief: str

    def __str__(self):
        return f"[MusicShare::title='{self.title}',musicUrl='{self.musicUrl}']"


class File(MessageModel):
    type = MessageModelTypes.File
    name: str
    size: Optional[int]

    def __str__(self):
        return f"[File::name='{self.name}']"


message_model = {
    "Source": Source,
    "Plain": Plain,
    "At": At,
    "AtAll": AtAll,
    "Face": Face,
    "Image": Image,
    "FlashImage": FlashImage,
    "Voice": Voice,
    "Xml": Xml,
    "Json": Json,
    "App": App,
    "Poke": Poke,
    "Dice": Dice,
    "MusicShare": MusicShare,
    "File": File
}
