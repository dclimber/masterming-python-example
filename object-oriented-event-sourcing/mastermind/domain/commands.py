import abc
import dataclasses

from mastermind.domain import value


@dataclasses.dataclass()
class GameCommand(abc.ABC):
    game_id: value.GameId


@dataclasses.dataclass()
class JoinGame(GameCommand):
    secret: value.Code
    total_attempts: int
    available_pegs: set[value.Code.Peg]


@dataclasses.dataclass()
class MakeGuess(GameCommand):
    guess: value.Code
