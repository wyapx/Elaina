from enum import Enum
from typing import Optional, List

from pydantic import BaseModel


class Sex(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"


class Friend(BaseModel):
    id: int
    nickname: str
    remark: Optional[str]


class Profile(BaseModel):
    nickname: str
    email: str
    age: int
    level: int
    sign: str
    sex: Sex


class FriendList(BaseModel):
    __root__: List[Friend]
