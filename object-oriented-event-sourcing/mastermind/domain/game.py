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

    def apply_event(self, event: events.GameEvent) -> "Game":
        if isinstance(event, events.GuessMade):
            return dataclasses.replace(self, attempts=self.attempts + 1)
        elif isinstance(event, events.GameWon):
            return WonGame()
        elif isinstance(event, events.GameLost):
            return LostGame()
        return self

    def execute(
        self, command: commands.GameCommand
    ) -> errors.GameError | NonEmptyList[events.GameEvent]:
        if isinstance(command, commands.MakeGuess):
            valid_guess = self.__valid_guess(command.game_id, command.guess)
            if isinstance(valid_guess, errors.GameError):
                return valid_guess

            feedback = self.__feedback_on(command.guess)
            result_events = NonEmptyList(
                [
                    events.GuessMade(
                        command.game_id,
                        value.Guess(command.guess, feedback),
                    )
                ]
            )

            if feedback.outcome == value.Feedback.Outcome.WON:
                result_events.append(events.GameWon(command.game_id))
            elif feedback.outcome == value.Feedback.Outcome.LOST:
                result_events.append(events.GameLost(command.game_id))

            return NonEmptyList(result_events)

        return errors.GameError(command.game_id)

    def __valid_guess(
        self, game_id: value.GameId, guess: value.Code
    ) -> None | errors.GameError:
        if len(guess.pegs) < len(self.secret.pegs):
            return errors.GuessTooShort(game_id, guess, len(self.secret.pegs))
        if len(guess.pegs) > len(self.secret.pegs):
            return errors.GuessTooLong(game_id, guess, len(self.secret.pegs))
        if not all(peg in self.available_pegs for peg in guess.pegs):
            return errors.InvalidPegInGuess(game_id, guess, self.available_pegs)
        return None

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


@dataclasses.dataclass()
class WonGame(Game):
    def apply_event(self, _: events.GameEvent) -> Self:
        return self

    def execute(
        self, command: commands.GameCommand
    ) -> errors.GameError | NonEmptyList[events.GameEvent]:
        return errors.GameAlreadyWon(command.game_id)


@dataclasses.dataclass()
class LostGame(Game):
    def apply_event(self, _: events.GameEvent) -> Self:
        return self

    def execute(
        self, command: commands.GameCommand
    ) -> errors.GameError | NonEmptyList[events.GameEvent]:
        return errors.GameAlreadyLost(command.game_id)
