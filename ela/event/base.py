from pydantic import BaseModel

from ela.component.friend import Friend


class BotEvent(BaseModel):
    type: str
    qq: int


class FriendEvent(BaseModel):
    type: str
    friend: Friend


class GroupEvent(BaseModel):
    type: str
