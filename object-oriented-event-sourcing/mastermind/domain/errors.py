import abc
import dataclasses

from mastermind.domain import value


@dataclasses.dataclass()
class GameError(abc.ABC):
    game_id: value.GameId


class GuessError(GameError):
    pass


class GameNotStarted(GuessError):
    pass
