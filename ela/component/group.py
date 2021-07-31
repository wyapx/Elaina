from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


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


class GroupFile(BaseModel):
    name: str
    path: str
    id: str
    length: int
    downloadTimes: int
    uploaderId: int
    uploadTime: int
    lastModifyTime: int
    downloadUrl: str
    sha1: str
    md5: str


class GroupFileShort(BaseModel):
    name: str
    id: str
    path: str
    isFile: bool


class GroupFileList(BaseModel):
    __root__: List[GroupFileShort] = []


class GroupList(BaseModel):
    __root__: List[Group]


class GroupMemberList(BaseModel):
    __root__: List[Member]
