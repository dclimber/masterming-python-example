import abc
import dataclasses

from mastermind.domain import value


@dataclasses.dataclass()
class GameError(abc.ABC):
    game_id: value.GameId


@dataclasses.dataclass()
class GameFinishedError(GameError):
    pass


@dataclasses.dataclass()
class GameAlreadyWon(GameFinishedError):
    pass


@dataclasses.dataclass()
class GameAlreadyLost(GameFinishedError):
    pass


@dataclasses.dataclass()
class GuessError(GameError):
    pass


@dataclasses.dataclass()
class GameNotStarted(GuessError):
    pass


@dataclasses.dataclass()
class GuessTooShort(GuessError):
    guess: value.Code
    required_length: int


@dataclasses.dataclass()
class GuessTooLong(GuessError):
    guess: value.Code
    required_length: int


@dataclasses.dataclass()
class InvalidPegInGuess(GuessError):
    guess: value.Code
    available_pegs: set[value.Code.Peg]
