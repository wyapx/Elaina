import asyncio
import logging
import secrets
from typing import Union, List, Dict, Callable

import aiohttp

from . import method
from .component.friend import FriendList, Profile
from .component.group import Group, GroupList, GroupMemberList, FileList, File
from .message.chain import MessageChain, CacheMessage
from .method import NewResponse
from .network import Network
from .types import T
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
    def session_key(self) -> str:
        return self._network.session_key

    @property
    def ws(self) -> aiohttp.ClientWebSocketResponse:
        if not self.__ws:
            raise RuntimeError("Application not running")
        return self.__ws[0]

    @ws.setter
    def ws(self, conn_list: List[aiohttp.ClientWebSocketResponse]):
        self.__ws = conn_list

    async def _send_req(self, command: str, content: method.BaseSession, *, subcommmand=None, return_obj=None):
        req_id = secrets.token_hex(8)
        data = method.Request(
            syncId=req_id,
            command=command,
            subCommand=subcommmand,
            content=content
        ).json()
        future = self._loop.create_future()
        self._msg_future[str(req_id)] = future
        logger.debug(data)
        await self.ws.send_str(data)
        logger.warning(f"command {command} was called")
        return assert_success(
            await future,
            return_obj
        )

    async def getMessageFromId(self, message_id: T.Source) -> CacheMessage:
        return CacheMessage(
            **(await self._send_req("messageFromId", method.GetInfoFromId(
                id=message_id,
                sessionKey=self.session_key
            ), return_obj="data"))
        )

    async def sendGroupMessage(
            self,
            group: T.Group,
            chain: T.Chain,
            *, quote_msg: T.Source = None
    ) -> int:
        if isinstance(chain, list):
            chain = MessageChain.parse_obj(await prepare_chain(self._network, "group", chain))
        msg_id = await self._send_req("sendGroupMessage", method.SendMessage(
            target=group,
            quote=quote_msg,
            messageChain=chain,
            sessionKey=self.session_key
        ), return_obj="messageId")
        if msg_id == -1:
            logger.warning("Message may not be sent")
        return msg_id

    async def sendFriendMessage(
            self,
            friend: T.Friend,
            chain: T.MessageType,
            *, quote_msg: T.MessageType = None
    ) -> int:
        if isinstance(chain, list):
            chain = MessageChain.parse_obj(await prepare_chain(self._network, "friend", chain))
        msg_id = await self._send_req("sendFriendMessage", method.SendMessage(
            target=friend,
            quote=quote_msg,
            messageChain=chain,
            sessionKey=self.session_key
        ), return_obj="messageId")
        if msg_id == -1:
            logger.warning("Message may not be sent")
        return msg_id

    async def sendTempMessage(
            self,
            group: T.Group,
            qq: int,
            chain: T.Chain,
            *, quote_msg: T.MessageType = None
    ) -> int:
        if isinstance(chain, list):
            chain = MessageChain.parse_obj(await prepare_chain(self._network, "temp", chain))
        msg_id = await self._send_req("sendTempMessage", method.SendTempMessage(
            qq=qq,
            group=group,
            quote=quote_msg,
            messageChain=chain,
            sessionKey=self.session_key
        ), return_obj="messageId")
        if msg_id == -1:
            logger.warning("Message may not be sent")
        return msg_id

    async def recallMessage(self, target: int):
        return await self._send_req("recall", method.GetInfoFromTarget(
            sessionKey=self.session_key,
            target=target
        ))

    async def setMemberPermission(self, group: T.Group, member: T.Member, is_admin: bool):
        return await self._send_req("memberAdmin", method.SetMemberPermission(
            sessionKey=self.session_key,
            target=group,
            memberId=member,
            assign=is_admin
        ))

    async def friendList(self) -> FriendList:
        return FriendList(
            __root__=await self._send_req("friendList", method.BaseSession(
                sessionKey=self.session_key
            ), return_obj="data")
        )

    async def groupList(self) -> GroupList:
        return GroupList(
            __root__=await self._send_req("groupList", method.BaseSession(
                sessionKey=self.session_key
            ), return_obj="data")
        )

    async def memberList(self, target: Union[int, Group]) -> GroupMemberList:
        return GroupMemberList(
            __root__=await self._send_req("memberList", method.GetInfoFromTarget(
                sessionKey=self.session_key,
                target=target
            ), return_obj="data")
        )

    async def botProfile(self) -> Profile:
        return Profile(
            **(await self._send_req("botProfile", method.BaseSession(
                sessionKey=self.session_key
            )))
        )

    async def friendProfile(self, target: int) -> Profile:
        return Profile(
            **(await self._send_req("friendProfile", method.GetInfoFromTarget(
                sessionKey=self.session_key,
                target=target
            )))
        )

    async def memberProfile(self, group: T.Group, member: T.Member) -> Profile:
        return Profile(
            **(await self._send_req("memberProfile", method.GetMemberProfile(
                sessionKey=self.session_key,
                target=group,
                memberId=member
            )))
        )

    async def fileList(self, target: [T.Group, T.Friend], parent_id="") -> FileList:
        return FileList(
            __root__=await self._send_req("file_list", method.GetFile(
                sessionKey=self.session_key,
                target=target,
                id=parent_id
            ), return_obj="data")
        )

    async def fileInfo(self, target: [T.Group, T.Member], file_id: str) -> File:
        return File(
            **(await self._send_req("file_info", method.GetFile(
                sessionKey=self.session_key,
                target=target,
                id=file_id
            )))
        )

    async def group_mkdir(self, target: T.Group, name: str, parent_id=""):
        return await self._send_req("file_mkdir", method.MakeDir(
            sessionKey=self.session_key,
            target=target,
            id=parent_id,
            directoryName=name
        ))

    async def group_move_file(self, target: T.Group, target_id: str, dst_id: str):
        return await self._send_req("file_move", method.MoveFile(
            sessionKey=self.session_key,
            target=target,
            id=target_id,
            moveTo=dst_id
        ))

    async def deleteFriend(self, target: T.Friend):
        return await self._send_req("deleteFriend", method.GetInfoFromTarget(
            sessionKey=self.session_key,
            target=target
        ))

    async def sendNudge(self, target: Union[T.Member, T.Friend], subject: T.Group = None):
        if not subject:
            subject = target
            kind = "Friend"
        else:
            kind = "Group"
        return await self._send_req("sendNudge", method.SendNudge(
            sessionKey=self.session_key,
            target=target,
            subject=subject,
            kind=kind
        ))

    async def muteMember(self, group: T.Group, member: T.Member, mute_sec=60):
        return await self._send_req("mute", method.MuteMember(
            sessionKey=self.session_key,
            target=group,
            memberId=member,
            time=mute_sec
        ))

    async def unmuteMember(self, group: T.Group, member: T.Member):
        return await self._send_req("unmute", method.GetMemberProfile(
            sessionKey=self.session_key,
            target=group,
            memberId=member
        ))

    async def kick(self, target: T.Group, member: T.Member, msg=None):
        return await self._send_req("kick", method.KickMember(
            sessionKey=self.session_key,
            target=target,
            memberId=member,
            msg=msg
        ))

    async def quit(self, target: T.Group):
        return await self._send_req("quit", method.GetInfoFromTarget(
            sessionKey=self.session_key,
            target=target
        ))

    async def muteAll(self, target: T.Group):
        return await self._send_req("muteAll", method.GetInfoFromTarget(
            sessionKey=self.session_key,
            target=target
        ))

    async def unmuteAll(self, target: T.Group):
        return await self._send_req("unmuteAll", method.GetInfoFromTarget(
            sessionKey=self.session_key,
            target=target
        ))

    async def setEssence(self, msg: T.Source):
        return await self._send_req("setEssence", method.GetInfoFromTarget(
            sessionKey=self.session_key,
            target=msg
        ))

    async def resp_newFriendRequestEvent(self, resp: Callable[[str], NewResponse]):
        return await self._send_req("resp_newFriendRequestEvent", resp(self.session_key))

    async def resp_memberJoinRequestEvent(self, resp: Callable[[str], NewResponse]):
        return await self._send_req("resp_memberJoinRequestEvent", resp(self.session_key))

    async def resp_botInvitedJoinGroupRequestEvent(self, resp: Callable[[str], NewResponse]):
        return await self._send_req("resp_botInvitedJoinGroupRequestEvent", resp(self.session_key))
