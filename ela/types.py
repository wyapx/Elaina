import random
from enum import Enum


class PokeType(str, Enum):
    SixSixSix = "SixSixSix"
    ShowLove = "ShowLove"
    Like = "Like"
    Heartbroken = "Heartbroken"
    FangDaZhao = "FangDaZhao"
    Poke = "Poke"

    def random_choice(self) -> 'PokeType':
        return random.choice([self.SixSixSix, self.ShowLove, self.Poke, self.Like, self.FangDaZhao, self.Heartbroken])
