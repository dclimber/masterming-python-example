import abc
import dataclasses

from mastermind.domain import value


@dataclasses.dataclass(frozen=True, eq=True)
class GameEvent(abc.ABC):
    game_id: value.GameId


@dataclasses.dataclass(frozen=True, eq=True)
class GameStarted(GameEvent):
    secret: value.Code
    total_attempts: int
    available_pegs: set[value.Code.Peg]


@dataclasses.dataclass(frozen=True, eq=True)
class GuessMade(GameEvent):
    guess: value.Guess


@dataclasses.dataclass(frozen=True, eq=True)
class GameWon(GameEvent):
    pass


@dataclasses.dataclass(frozen=True, eq=True)
class GameLost(GameEvent):
    pass
