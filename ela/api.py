import asyncio
import logging
from random import randint
from typing import Type, Union, List, Dict

import aiohttp

from . import method
from .component.friend import Friend, FriendList, Profile
from .component.group import Group, GroupList, GroupMemberList
from .message.base import MessageModel, RemoteResource, UnpreparedResource
from .message.chain import MessageChain
from .message.models import Source
from .message.type import GroupMessage, FriendMessage, TempMessage
from .network import Network
from .utils import prepare_chain, assert_success

logger = logging.getLogger(__name__)


class API:
    def __init__(self, baseurl: str, qq: int, verify_key: str, *, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        self._network = Network(baseurl, qq, verify_key, loop=loop)
        self._loop = loop
        self._msg_future: Dict[str, asyncio.Future] = {}
        self.__ws: List[aiohttp.ClientWebSocketResponse] = []

    @property
    def ws(self) -> aiohttp.ClientWebSocketResponse:
        if not self.__ws:
            raise RuntimeError("Application not running")
        return self.__ws[0]

    @ws.setter
    def ws(self, conn_list: List[aiohttp.ClientWebSocketResponse]):
        self.__ws = conn_list

    async def _send_req(self, command: str, content: method.BaseSession, *, subcommmand=None, return_obj=None):
        req_id = randint(1, 1024)
        data = method.Request(
            syncId=str(req_id),
            command=command,
            subCommand=subcommmand,
            content=content
        ).json()
        future = self._loop.create_future()
        self._msg_future[str(req_id)] = future
        await self.ws.send_str(data)
        logger.debug(f"command {command} was called")
        return assert_success(
            await future,
            return_obj
        )

    async def getMessageFromId(
            self,
            message_id: int,
            msgtype: Type[Union[GroupMessage, FriendMessage, TempMessage]]
    ) -> Union[GroupMessage, FriendMessage, TempMessage]:
        return msgtype(
            **(await self._send_req("messageFromId", method.GetInfoFromTarget(
                target=message_id,
                sessionKey=self._network.session_key
            )))
        )

    async def sendGroupMessage(
            self,
            group: Union[int, Group],
            chain: Union[MessageChain, List[Union[MessageModel, RemoteResource, UnpreparedResource]]],
            *, quote_msg: Union[int, Source] = None
    ) -> int:
        if isinstance(chain, list):
            chain = MessageChain.parse_obj(await prepare_chain(self._network, "group", chain))
        msg_id = await self._send_req("sendGroupMessage", method.SendMessage(
            target=group,
            quote=quote_msg,
            messageChain=chain,
            sessionKey=self._network.session_key
        ), return_obj="messageId")
        if msg_id == -1:
            logger.warning("Message may not be sent")
        return msg_id

    async def sendFriendMessage(
            self,
            friend: Union[int, Friend],
            chain: Union[MessageChain, List[Union[MessageModel, RemoteResource, UnpreparedResource]]],
            *, quote_msg: Union[int, Source] = None
    ) -> int:
        if isinstance(chain, list):
            chain = MessageChain.parse_obj(await prepare_chain(self._network, "friend", chain))
        msg_id = await self._send_req("sendFriendMessage", method.SendMessage(
            target=friend,
            quote=quote_msg,
            messageChain=chain,
            sessionKey=self._network.session_key
        ), return_obj="messageId")
        if msg_id == -1:
            logger.warning("Message may not be sent")
        return msg_id

    async def sendTempMessage(
            self,
            group: Union[int, Group],
            qq: int,
            chain: Union[MessageChain, List[Union[MessageModel, RemoteResource, UnpreparedResource]]],
            *, quote_msg: Union[int, Source] = None
    ) -> int:
        if isinstance(chain, list):
            chain = MessageChain.parse_obj(await prepare_chain(self._network, "temp", chain))
        msg_id = await self._send_req("sendTempMessage", method.SendTempMessage(
            qq=qq,
            group=group,
            quote=quote_msg,
            messageChain=chain,
            sessionKey=self._network.session_key
        ), return_obj="messageId")
        if msg_id == -1:
            logger.warning("Message may not be sent")
        return msg_id

    async def recallMessage(self, target: int):
        return assert_success(
            await self._send_req("recall", method.GetInfoFromTarget(
                sessionKey=self._network.session_key,
                target=target
            ))
        )

    async def friendList(self) -> FriendList:
        return FriendList(
            __root__=await self._send_req("friendList", method.BaseSession(
                sessionKey=self._network.session_key
            ), return_obj="data")
        )

    async def groupList(self) -> GroupList:
        return GroupList(
            __root__=await self._send_req("groupList", method.BaseSession(
                sessionKey=self._network.session_key
            ), return_obj="data")
        )

    async def memberList(self, target: Union[int, Group]) -> GroupMemberList:
        return GroupMemberList(
            __root__=await self._send_req("memberList", method.GetInfoFromTarget(
                sessionKey=self._network.session_key,
                target=target
            ), return_obj="data")
        )

    async def botProfile(self) -> Profile:
        return Profile(
            **(await self._send_req("botProfile", method.BaseSession(
                sessionKey=self._network.session_key
            )))
        )

    async def friendProfile(self, target: int) -> Profile:
        return Profile(
            **(await self._send_req("friendProfile", method.GetInfoFromTarget(
                sessionKey=self._network.session_key,
                target=target
            )))
        )

    async def memberProfile(self, group: Union[int, Group], member: int) -> Profile:
        return Profile(
            **(await self._send_req("memberProfile", method.GetMemberProfile(
                sessionKey=self._network.session_key,
                target=group,
                memberId=member
            )))
        )
