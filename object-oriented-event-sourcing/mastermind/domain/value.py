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


@dataclasses.dataclass()
class GameId:
    value: str


@dataclasses.dataclass(init=False)
class Feedback:
    class Outcome(enum.IntEnum):
        IN_PROGRESS = 1
        WON = 2
        LOST = 3

    class Peg(enum.Enum):
        BLACK = "Black"
        WHITE = "White"

    outcome: Outcome
    pegs: list[Peg]

    def __init__(self, outcome: Outcome, *pegs: Peg) -> None:
        self.outcome = outcome
        self.pegs = [peg for peg in pegs]


@dataclasses.dataclass()
class Guess:
    code: Code
    feedback: Feedback
