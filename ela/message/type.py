from pydantic import BaseModel
from typing import Optional, Union
from .chain import MessageChain
from .models import Source
from ela.component.friend import Friend
from ela.component.group import Member, Group


class Client(BaseModel):
    id: int
    platform: Optional[str]


class MessageType(BaseModel):
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


class FriendMessage(MessageType):
    type: str = "FriendMessage"
    sender: Friend
    

class GroupMessage(MessageType):
    type: str = "GroupMessage"
    sender: Member


class TempMessage(MessageType):
    type: str = "TempMessage"
    sender: Member


class StrangerMessage(MessageType):
    type = "StrangerMessage"
    sender: Friend


class OtherClientMessage(MessageType):
    type = "OtherClientMessage"
    sender: Client


message_type = {
    "FriendMessage": FriendMessage,
    "GroupMessage": GroupMessage,
    "TempMessage": TempMessage,
    "StrangerMessage": StrangerMessage,
    "OtherClientMessage": OtherClientMessage
}
