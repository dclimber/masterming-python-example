import abc
import dataclasses
from collections import UserList
from typing import Generic, Iterable, Self, TypeVar

from mastermind.domain import commands, errors, events, value

T = TypeVar("T")


class NonEmptyList(UserList, Generic[T]):
    def __init__(self, iterable: Iterable):
        if len(list(iterable)) == 0:
            raise ValueError("NonEmptyList cannot be empty!")
        super().__init__(iterable)


class Game(abc.ABC):
    @abc.abstractmethod
    def apply_event(self, event: events.GameEvent) -> Self:
        raise NotImplementedError()

    @abc.abstractmethod
    def execute(
        self, command: commands.GameCommand
    ) -> errors.GameError | NonEmptyList[events.GameEvent]:
        raise NotImplementedError()


class NotStartedGame(Game):

    def apply_event(self, event: events.GameEvent) -> Game:
        if isinstance(event, events.GameStarted):
            return StartedGame(
                event.secret, 0, event.total_attempts, event.available_pegs
            )
        return self

    def execute(
        self, command: commands.GameCommand
    ) -> errors.GameError | NonEmptyList[events.GameEvent]:
        if isinstance(command, commands.JoinGame):
            return NonEmptyList(
                [
                    events.GameStarted(
                        command.game_id,
                        command.secret,
                        command.total_attempts,
                        command.available_pegs,
                    )
                ]
            )
        return errors.GameNotStarted(command.game_id)


@dataclasses.dataclass()
class StartedGame(Game):
    secret: value.Code
    attempts: int
    total_attempts: int
    available_pegs: set[value.Code.Peg]

    def apply_event(self, event: events.GameEvent) -> Self:
        return self

    def execute(
        self, command: commands.GameCommand
    ) -> errors.GameError | NonEmptyList[events.GameEvent]:
        return errors.GameError(command.game_id)
