from typing import Optional

from pydantic import BaseModel

from ela.message.chain import MessageChain


class BaseSession(BaseModel):
    sessionKey: str


class Request(BaseModel):
    syncId: str
    command: str
    subCommand: Optional[str]
    content: BaseSession


class SendMessage(BaseSession):
    target: int
    quote: Optional[int]
    messageChain: MessageChain


class SendTempMessage(BaseSession):
    qq: int
    group: int
    quote: Optional[int]
    messageChain: MessageChain


class GetInfoFromTarget(BaseSession):
    target: int


class GetMemberProfile(GetInfoFromTarget):
    memberId: int


class GetFileList(GetInfoFromTarget):
    id: str = ""
    group: Optional[int]
    qq: Optional[int]
    withDownloadInfo: bool = True


class MuteMember(GetMemberProfile):
    time: int
