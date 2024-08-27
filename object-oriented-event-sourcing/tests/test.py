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
