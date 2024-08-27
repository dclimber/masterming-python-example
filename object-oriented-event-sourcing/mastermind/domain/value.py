import dataclasses
import enum
from typing import Iterable, cast


@dataclasses.dataclass()
class Code:
    @dataclasses.dataclass(frozen=True, eq=True)
    class Peg:
        name: str

    pegs: list[Peg]

    def __init__(self, *pegs: Peg | str) -> None:
        if all(isinstance(peg, Code.Peg) for peg in pegs):
            self.pegs = list(cast(Iterable[Code.Peg], pegs))
        elif all(isinstance(peg, str) for peg in pegs):
            self.pegs = [Code.Peg(name=peg) for peg in cast(list[str], pegs)]
        else:
            raise ValueError("All arguments must be either Peg objects or strings")

    @property
    def length(self) -> int:
        return len(self.pegs)


def set_of_pegs(*pegs: str) -> set[Code.Peg]:
    return set(Code.Peg(peg) for peg in pegs)


class GameId:
    def __init__(self, value: str) -> None:
        self.__value: str = value

    @property
    def value(self) -> str:
        return self.__value


@dataclasses.dataclass()
class Feedback:
    class Outcome(enum.IntEnum):
        IN_PROGRESS = 1
        WON = 2
        LOST = 3

    class Peg(enum.Enum):
        BLACK = "Black"
        WHITE = "White"

    outcome: Outcome
    pegs: list[Peg] = dataclasses.field(default_factory=list)


@dataclasses.dataclass()
class Guess:
    code: Code
    feedback: Feedback
