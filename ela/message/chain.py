import time

from .models import message_model
from .base import MessageModel, RemoteResource, MessageModelTypes
from typing import List, Union, Type, Optional, Any
from pydantic import BaseModel, validator


class MessageChain(BaseModel):
    __root__: List[Any] = []

    @validator("__root__")
    def parse_obj(cls, obj):
        res = []
        for item in obj:
            if isinstance(item, dict):
                res.append(message_model[item["type"]].parse_obj(item))
            elif isinstance(item, MessageModel):
                res.append(item)
            else:
                raise ValueError(item)
        return res

    def get_first_model(self, model_type: Type[Union[RemoteResource, MessageModel]])\
            -> Union[MessageModel, RemoteResource, None]:
        for item in self.__root__:
            if isinstance(item, model_type):
                return item

    def __add__(self, value):
        if isinstance(value, MessageModel):
            self.__root__.append(value)
            return self
        elif isinstance(value, MessageChain):
            self.__root__ += value.__root__
            return self

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index):
        return self.__root__[index]

    def __str__(self):
        return "".join([str(item) for item in self.__root__[1:]])

    __repr__ = __str__


class Quote(MessageModel):
    type: MessageModelTypes = "Quote"
    id: int
    groupId: int
    senderId: int
    targetId: int
    origin: MessageChain

    def __str__(self):
        return f"[Quote id={self.id}]"


class NodeInfo(BaseModel):
    senderId: int
    time: int
    senderName: Optional[str]
    messageChain: Optional[MessageChain]
    messageId: Optional[int]


class ForwardMessage(MessageModel):
    type: MessageModelTypes = "Forward"
    nodeList: List[NodeInfo] = []

    def create_node(self,
                    sender_id: int,
                    chain: List[Union[RemoteResource, MessageModel]] = None,
                    *, name=None, time_=-1, message_id=None):
        if time_ == -1:
            time_ = int(time.time())
        assert chain or message_id
        self.nodeList.append(
            NodeInfo(
                senderId=sender_id,
                time=time_,
                senderName=name,
                messageChain=chain,
                messageId=message_id
            )
        )

    def add_message(self, sender, chain: List[Union[RemoteResource, MessageModel]] = None, message_id=None):
        """
        :type sender: mpy.component.group.Member
        :type chain:
        :type message_id: int
        :return: None
        """
        self.create_node(sender.id, chain=chain, name=sender.memberName, message_id=message_id)

    def add_node(self, node: NodeInfo):
        self.nodeList.append(node)


message_model["Forward"] = ForwardMessage
message_model["Quote"] = Quote
