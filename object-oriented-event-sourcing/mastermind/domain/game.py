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

    def apply_event(self, _: events.GameEvent) -> Self:
        return self

    def execute(
        self, command: commands.GameCommand
    ) -> errors.GameError | NonEmptyList[events.GameEvent]:
        if isinstance(command, commands.MakeGuess):

            feedback = self.__feedback_on(command.guess)
            result_events = [
                events.GuessMade(
                    command.game_id,
                    value.Guess(command.guess, feedback),
                )
            ]

            return NonEmptyList(result_events)

        return errors.GameError(command.game_id)

    def __feedback_on(self, guess: value.Code) -> value.Feedback:
        # Exact hits (correct color and position)
        exact_hits = [
            peg
            for peg, secret_peg in zip(guess.pegs, self.secret.pegs)
            if peg == secret_peg
        ]

        # Remove exact hits from consideration for color hits
        remaining_secret_pegs = [
            secret_peg
            for secret_peg, peg in zip(self.secret.pegs, guess.pegs)
            if peg != secret_peg
        ]
        remaining_guess_pegs = [
            peg
            for peg, secret_peg in zip(guess.pegs, self.secret.pegs)
            if peg != secret_peg
        ]

        # Color hits (correct color but wrong position)
        color_hits = []
        for peg in remaining_guess_pegs:
            if peg in remaining_secret_pegs:
                color_hits.append(peg)
                remaining_secret_pegs.remove(peg)

        # Determine the game outcome
        outcome = (
            value.Feedback.Outcome.WON
            if len(exact_hits) == len(self.secret.pegs)
            else (
                value.Feedback.Outcome.LOST
                if self.attempts + 1 >= self.total_attempts
                else value.Feedback.Outcome.IN_PROGRESS
            )
        )

        # Convert exact hits and color hits to their corresponding peg feedback
        feedback_pegs = [value.Feedback.Peg.BLACK] * len(exact_hits) + [
            value.Feedback.Peg.WHITE
        ] * len(color_hits)

        return value.Feedback(outcome, *feedback_pegs)
