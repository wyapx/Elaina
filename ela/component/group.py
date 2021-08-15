import hashlib
import os
from enum import Enum
from typing import List, Optional, Iterable

import aiohttp
from pydantic import BaseModel, HttpUrl


class Permission(str, Enum):
    Member = "MEMBER"
    Administrator = "ADMINISTRATOR"
    Owner = "OWNER"


class GroupHonorAction(str, Enum):
    achieve = "achieve"
    lose = "lose"


class Group(BaseModel):
    id: int
    name: str
    permission: Permission

    def __int__(self):
        return self.id

    def __repr__(self):
        return f"<Group id={self.id} name='{self.name}' permission={self.permission.name}>"

    def getAvatarUrl(self) -> str:
        return f'https://p.qlogo.cn/gh/{self.id}/{self.id}/'


class Member(BaseModel):
    id: int
    memberName: str
    specialTitle: Optional[str]
    joinTimestamp: Optional[int]
    lastSpeakTimestamp: Optional[int]
    muteTimeRemaining: Optional[int]
    permission: Permission
    group: Group

    def __int__(self):
        return self.id

    def __str__(self):
        return self.memberName

    def __repr__(self):
        return f"<GroupMember id={self.id} group={self.group} permission={self.permission} group={self.group.id}>"

    def getAvatarUrl(self) -> str:
        return f'https://q4.qlogo.cn/g?b=qq&nk={self.id}&s=140'


class MemberChangeableSetting(BaseModel):
    name: str
    specialTitle: str

    def modify(self, **kwargs):
        for i in ("name", "kwargs"):
            if i in kwargs:
                setattr(self, i, kwargs[i])
        return self


class GroupSetting(BaseModel):
    name: str
    announcement: str
    confessTalk: bool
    allowMemberInvite: bool
    autoApprove: bool
    anonymousChat: bool

    def modify(self, **kwargs):
        for i in ("name",
                  "announcement",
                  "confessTalk",
                  "allowMemberInvite",
                  "autoApprove",
                  "anonymousChat"
                  ):
            if i in kwargs:
                setattr(self, i, kwargs[i])
        return self


class DownloadInfo(BaseModel):
    sha1: str
    md5: str
    url: HttpUrl


class Contact(BaseModel):
    id: int
    name: str
    permission: Permission


class GroupFile(BaseModel):
    name: str
    path: str
    id: str
    contact: Contact
    isFile: bool
    isDirectory: bool
    downloadInfo: Optional[DownloadInfo]

    @staticmethod
    def __remove_file(fd, path: str):
        fd.close()
        os.remove(path)

    async def download_file(self, save_path: str, verify_file=False):
        if not self.downloadInfo:
            raise AttributeError("downloadInfo not found")
        if verify_file:
            vf = hashlib.sha1()
        else:
            vf = None
        fd = open(save_path, "wb")
        try:
            async with aiohttp.request("GET", self.downloadInfo.url) as resp:
                async for bl in resp.content:
                    if vf:
                        vf.update(bl)
                    fd.write(bl)
        except:
            self.__remove_file(fd, save_path)
            raise
        if verify_file:
            if vf.hexdigest() != self.downloadInfo.sha1.lower():
                self.__remove_file(fd, save_path)
                raise NotImplementedError(vf.hexdigest(), self.downloadInfo.sha1.lower(), "not match")
            fd.close()


class GroupFileList(BaseModel):
    __root__: List[GroupFile]

    def __iter__(self) -> Iterable[GroupFile]:
        yield from self.__root__


class GroupList(BaseModel):
    __root__: List[Group]

    def __iter__(self) -> Iterable[Group]:
        yield from self.__root__


class GroupMemberList(BaseModel):
    __root__: List[Member]

    def __iter__(self) -> Iterable[Member]:
        yield from self.__root__