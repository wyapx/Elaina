from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel

from ela.component.friend import Friend
from ela.component.group import Member, Group
from .base import Client
from .chain import MessageChain
from .models import Source


class BaseMessageType(BaseModel):
    type: str
    messageChain: Optional[MessageChain]
    sender: Union[Friend, Member, Client]

    def __eq__(self, other):
        return str(self.messageChain) == other

    @property
    def source(self) -> Optional[Source]:
        if len(self.messageChain):
            return self.messageChain[0]

    @property
    def group(self) -> Optional[Group]:
        if isinstance(self.sender, Member):
            return self.sender.group
        return None


class FriendMessage(BaseMessageType):
    type: str = "FriendMessage"
    sender: Friend


class GroupMessage(BaseMessageType):
    type: str = "GroupMessage"
    sender: Member


class TempMessage(BaseMessageType):
    type: str = "TempMessage"
    sender: Member


class StrangerMessage(BaseMessageType):
    type = "StrangerMessage"
    sender: Friend


class OtherClientMessage(BaseMessageType):
    type = "OtherClientMessage"
    sender: Client


class MessageType(Enum):
    FriendMessage = FriendMessage,
    GroupMessage = GroupMessage,
    TempMessage = TempMessage,
    StrangerMessage = StrangerMessage,
    OtherClientMessage = OtherClientMessage

    @classmethod
    def exists(cls, item: str) -> bool:
        return item in cls.__members__

    @classmethod
    def to_message(cls, name: str, data: dict) -> BaseMessageType:
        return getattr(cls, name).value[0](**data)
