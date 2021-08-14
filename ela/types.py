import random
from typing import Union, List
from .component.group import Group, Member
from .component.friend import Friend
from enum import Enum

from .message.base import MessageModel, RemoteResource, UnpreparedResource
from .message.chain import MessageChain
from .message.type import GroupMessage, FriendMessage, TempMessage
from .message.models import Source


class T:
    Group = Union[Group, int]
    Friend = Union[Friend, int]
    Source = Union[Source, int]
    Member = int
    Chain = Union[MessageChain, List[Union[MessageModel, RemoteResource, UnpreparedResource]]]
    MessageType = Union[GroupMessage, FriendMessage, TempMessage]


class PokeType(str, Enum):
    SixSixSix = "SixSixSix"
    ShowLove = "ShowLove"
    Like = "Like"
    Heartbroken = "Heartbroken"
    FangDaZhao = "FangDaZhao"
    Poke = "Poke"

    def random_choice(self) -> 'PokeType':
        return random.choice([self.SixSixSix, self.ShowLove, self.Poke, self.Like, self.FangDaZhao, self.Heartbroken])
