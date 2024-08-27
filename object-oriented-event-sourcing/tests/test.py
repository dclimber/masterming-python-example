import unittest
import uuid

from mastermind.domain import commands, errors, events, game, value


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

    def test_the_game_is_won_if_the_secret_is_guessed(self) -> None:
        entity = self.game_of(
            events.GameStarted(
                self.game_id, self.secret, self.total_attempts, self.available_pegs
            )
        )
        command = commands.MakeGuess(self.game_id, self.secret)

        result = entity.execute(command)

        self.assertEqual(
            result,
            [
                events.GuessMade(
                    self.game_id,
                    value.Guess(
                        self.secret,
                        value.Feedback(
                            value.Feedback.Outcome.WON,
                            value.Feedback.Peg.BLACK,
                            value.Feedback.Peg.BLACK,
                            value.Feedback.Peg.BLACK,
                            value.Feedback.Peg.BLACK,
                        ),
                    ),
                ),
                events.GameWon(self.game_id),
            ],
        )

    def test_the_game_can_no_longer_be_played_once_won(self) -> None:
        starting_events = [
            events.GameStarted(
                self.game_id, self.secret, self.total_attempts, self.available_pegs
            )
        ]
        entity = self.game_of(*starting_events)

        win_command = commands.MakeGuess(self.game_id, self.secret)
        result = entity.execute(win_command)
        updated_events = starting_events + result
        updated_game = self.game_of(*updated_events)

        error = updated_game.execute(commands.MakeGuess(self.game_id, self.secret))
        self.assertIsInstance(error, errors.GameAlreadyWon)

    def test_the_game_is_lost_if_the_secret_is_not_guessed_within_attempts(
        self,
    ) -> None:
        wrong_code = value.Code("Purple", "Purple", "Purple", "Purple")
        entity = self.game_of(
            events.GameStarted(self.game_id, self.secret, 3, self.available_pegs),
            events.GuessMade(
                self.game_id,
                value.Guess(
                    wrong_code, value.Feedback(value.Feedback.Outcome.IN_PROGRESS)
                ),
            ),
            events.GuessMade(
                self.game_id,
                value.Guess(
                    wrong_code, value.Feedback(value.Feedback.Outcome.IN_PROGRESS)
                ),
            ),
        )

        command = commands.MakeGuess(self.game_id, wrong_code)
        result = entity.execute(command)

        self.assertEqual(
            result,
            [
                events.GuessMade(
                    self.game_id,
                    value.Guess(
                        wrong_code, value.Feedback(value.Feedback.Outcome.LOST)
                    ),
                ),
                events.GameLost(self.game_id),
            ],
        )

    def test_the_game_can_no_longer_be_played_once_lost(self) -> None:
        wrong_code = value.Code("Purple", "Purple", "Purple", "Purple")
        starting_events = [
            events.GameStarted(self.game_id, self.secret, 1, self.available_pegs)
        ]
        entity = self.game_of(*starting_events)

        lose_command = commands.MakeGuess(self.game_id, wrong_code)
        result = entity.execute(lose_command)

        updated_events = starting_events + result
        updated_game = self.game_of(*updated_events)

        error = updated_game.execute(commands.MakeGuess(self.game_id, self.secret))
        self.assertIsInstance(error, errors.GameAlreadyLost)

    def test_the_game_cannot_be_played_if_not_started(self) -> None:
        code = value.Code("Red", "Purple", "Red", "Purple")
        entity = game.NotStartedGame()

        error = entity.execute(commands.MakeGuess(self.game_id, code))
        self.assertIsInstance(error, errors.GameNotStarted)

    def test_the_guess_length_cannot_be_shorter_than_the_secret(self) -> None:
        short_code = value.Code("Purple", "Purple", "Purple")
        entity = self.game_of(
            events.GameStarted(
                self.game_id, self.secret, self.total_attempts, self.available_pegs
            )
        )

        error = entity.execute(commands.MakeGuess(self.game_id, short_code))
        self.assertIsInstance(error, errors.GuessTooShort)

    def test_the_guess_length_cannot_be_longer_than_the_secret(self) -> None:
        long_code = value.Code("Purple", "Purple", "Purple", "Purple", "Purple")
        entity = self.game_of(
            events.GameStarted(
                self.game_id, self.secret, self.total_attempts, self.available_pegs
            )
        )

        error = entity.execute(commands.MakeGuess(self.game_id, long_code))
        self.assertIsInstance(error, errors.GuessTooLong)

    def test_it_rejects_pegs_that_the_game_was_not_started_with(self) -> None:
        secret = value.Code("Red", "Green", "Blue", "Blue")
        limited_pegs = value.set_of_pegs("Red", "Green", "Blue")
        entity = self.game_of(
            events.GameStarted(self.game_id, secret, self.total_attempts, limited_pegs)
        )
        invalid_guess = value.Code("Red", "Green", "Blue", "Yellow")

        error = entity.execute(commands.MakeGuess(self.game_id, invalid_guess))
        self.assertIsInstance(error, errors.InvalidPegInGuess)
