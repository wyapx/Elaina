import time
from typing import List, Union, Type, Optional, Any, Tuple, Generator, Iterable

from pydantic import BaseModel, validator

from .base import MessageModel, RemoteResource, MessageModelTypes, Unprepared, UniqueModel
from .models import message_model, Source

MODEL_ARGS = Type[Union[RemoteResource, MessageModel]]


class MessageChain(BaseModel):
    __root__: List[Any]

    @validator("__root__")
    def create(cls, obj):
        ret = []
        with_unique = None
        for item in obj:
            if isinstance(item, dict):
                ret.append(message_model[item["type"]].parse_obj(item))
            elif isinstance(item, MessageModel):
                ret.append(item)
            else:
                raise ValueError(item)
            if isinstance(ret[-1], UniqueModel) and with_unique is None:  # todo: optimized
                with_unique = True
            elif isinstance(ret[-1], MessageModel) and not with_unique:
                with_unique = False
            else:
                raise ValueError("UniqueModel detect, but other model found")
        return ret

    def get_first_model(self, model_type: Union[Tuple[MODEL_ARGS], MODEL_ARGS]) \
            -> Union[MessageModel, RemoteResource, None]:
        for item in self:
            if isinstance(item, model_type):
                return item

    def get_all_model(self, model_type: Union[Tuple[MODEL_ARGS], MODEL_ARGS]) \
            -> Generator[Union[RemoteResource, MessageModel], None, None]:
        for item in self:
            if isinstance(item, model_type):
                yield item

    def get_source(self) -> Optional[Source]:
        if Source in self:
            return self.__root__[0]

    def get_forward(self) -> Optional[List["MessageNode"]]:
        if Forward in self:
            return self.get_first_model(Forward).nodeList

    def get_quote(self) -> Optional["Quote"]:
        return self.get_first_model(Quote)

    def __add__(self, value):
        if isinstance(value, MessageModel):
            self.__root__.append(value)
        elif isinstance(value, MessageChain):
            self.__root__ += value.__root__
        return self

    def __iter__(self):
        if Source in self:
            yield from self.__root__[1:]
        else:
            yield from self.__root__

    def __getitem__(self, index):
        return self.__root__[index]

    def __len__(self):
        return len(self.__root__)

    def __str__(self):
        return "".join([str(item) for item in self])

    def __contains__(self, item):
        return any(isinstance(e, item) for e in self.__root__)

    __repr__ = __str__


class CacheMessage(BaseModel):
    type: str
    messageChain: MessageChain


class Quote(MessageModel):
    type = MessageModelTypes.Quote
    id: int
    groupId: int
    senderId: int
    targetId: int
    origin: MessageChain

    def __str__(self):
        return f"[Quote::id={self.id}]"


class MessageNode(BaseModel):
    senderId: int
    time: int
    senderName: Optional[str]
    messageChain: Optional[MessageChain]
    messageId: Optional[int]

    def __repr__(self):
        return f'[Node::sender="{self.senderName}({self.senderId})",time="{self.time}"]'


class ForwardMessage(Unprepared):
    def __init__(self, chain: Optional[List[Tuple[int, str, Union[list, int]]]] = None):
        """
        chain format:
        [
            (uin, name, msg_id), # or
            (uin, name, MessageChain)
        ]
        """
        self._raw_chain = chain

    async def prepare(self, network, utype) -> "Forward":
        msg = Forward()
        for node in self._raw_chain:
            uin, name, data = node
            print(node)
            if isinstance(data, int):
                msg.create_node(uin, message_id=data, name=name)
            elif isinstance(data, list):
                chain = []
                for component in data:
                    if isinstance(component, Unprepared):
                        chain.append(await component.prepare(network, utype))
                    else:
                        chain.append(component)
                msg.create_node(uin, chain=chain, name=name)
            else:
                raise TypeError(data)
        return msg


class Forward(UniqueModel):
    type = MessageModelTypes.Forward
    nodeList: List[MessageNode] = []

    def create_node(self,
                    sender_id: int,
                    chain: Union[MessageChain, List[MessageModel]] = None,
                    *, name=None, time_=-1, message_id=None):
        if time_ == -1:
            time_ = int(time.time())
        assert chain or message_id
        self.nodeList.append(
            MessageNode(
                senderId=sender_id,
                time=time_,
                senderName=name,
                messageChain=chain,
                messageId=message_id
            )
        )

    def add_message(self, sender, chain: List[Union[RemoteResource, MessageModel]] = None, message_id=None):
        """
        :type sender: ela.component.group.Member
        :type chain:
        :type message_id: int
        :return: None
        """
        self.create_node(sender.id, chain=chain, name=sender.memberName, message_id=message_id)

    def add_node(self, node: MessageNode):
        self.nodeList.append(node)

    def __iter__(self) -> Iterable[MessageNode]:
        yield from self.nodeList


message_model["Forward"] = Forward
message_model["Quote"] = Quote
