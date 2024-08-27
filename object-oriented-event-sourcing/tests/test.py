import unittest
import uuid

from mastermind.domain import commands, events, game, value


def any_game_id() -> value.GameId:
    return value.GameId(str(uuid.uuid4()))


class TestGameExamples(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.game_id = any_game_id()
        self.secret = value.Code("Red", "Green", "Blue", "Yellow")
        self.total_attempts = 12
        self.available_pegs = value.set_of_pegs(
            "Red", "Green", "Blue", "Yellow", "Purple", "Pink"
        )

    @staticmethod
    def game_of(*events: events.GameEvent) -> game.Game:
        entity = game.NotStartedGame()
        for event in events:
            entity = entity.apply_event(event)
        return entity

    def test_it_starts_the_game(self) -> None:
        expected = [
            events.GameStarted(
                self.game_id, self.secret, self.total_attempts, self.available_pegs
            )
        ]
        command = commands.JoinGame(
            self.game_id, self.secret, self.total_attempts, self.available_pegs
        )
        not_started_game = game.NotStartedGame()

        result = not_started_game.execute(command)

        self.assertEqual(result, expected)

    def test_it_makes_a_guess(self) -> None:
        entity = TestGameExamples.game_of(
            events.GameStarted(
                self.game_id, self.secret, self.total_attempts, self.available_pegs
            )
        )
        command = commands.MakeGuess(
            self.game_id, value.Code("Purple", "Purple", "Purple", "Purple")
        )

        result = entity.execute(command)

        self.assertEqual(
            result,
            [
                events.GuessMade(
                    self.game_id,
                    value.Guess(
                        value.Code("Purple", "Purple", "Purple", "Purple"),
                        value.Feedback(value.Feedback.Outcome.IN_PROGRESS),
                    ),
                )
            ],
        )

    def test_it_gives_feedback_on_the_guess(self) -> None:
        guess_examples: list[tuple[str, value.Code, value.Code, value.Feedback]] = [
            (
                "it gives a black peg for each code peg on the correct position",
                value.Code("Red", "Green", "Blue", "Yellow"),
                value.Code("Red", "Purple", "Blue", "Purple"),
                value.Feedback(
                    value.Feedback.Outcome.IN_PROGRESS,
                    value.Feedback.Peg.BLACK,
                    value.Feedback.Peg.BLACK,
                ),
            ),
            (
                "it gives no black peg for code peg duplicated on a wrong position",
                value.Code("Red", "Green", "Blue", "Yellow"),
                value.Code("Red", "Red", "Purple", "Purple"),
                value.Feedback(
                    value.Feedback.Outcome.IN_PROGRESS, value.Feedback.Peg.BLACK
                ),
            ),
            (
                (
                    "it gives a white peg for code peg that is part of the code but is"
                    " placed on a wrong position"
                ),
                value.Code("Red", "Green", "Blue", "Yellow"),
                value.Code("Purple", "Red", "Purple", "Purple"),
                value.Feedback(
                    value.Feedback.Outcome.IN_PROGRESS, value.Feedback.Peg.WHITE
                ),
            ),
            (
                "it gives no white peg for code peg duplicated on a wrong position",
                value.Code("Red", "Green", "Blue", "Yellow"),
                value.Code("Purple", "Red", "Red", "Purple"),
                value.Feedback(
                    value.Feedback.Outcome.IN_PROGRESS, value.Feedback.Peg.WHITE
                ),
            ),
            (
                "it gives a white peg for each code peg on a wrong position",
                value.Code("Red", "Green", "Blue", "Red"),
                value.Code("Purple", "Red", "Red", "Purple"),
                value.Feedback(
                    value.Feedback.Outcome.IN_PROGRESS,
                    value.Feedback.Peg.WHITE,
                    value.Feedback.Peg.WHITE,
                ),
            ),
        ]

        for description, secret, guess, feedback in guess_examples:
            with self.subTest(description=description):
                entity = self.game_of(
                    events.GameStarted(
                        self.game_id, secret, self.total_attempts, self.available_pegs
                    )
                )
                command = commands.MakeGuess(self.game_id, guess)

                result = entity.execute(command)

                self.assertEqual(
                    result,
                    game.NonEmptyList(
                        [
                            events.GuessMade(
                                self.game_id,
                                value.Guess(guess, feedback),
                            )
                        ]
                    ),
                )
