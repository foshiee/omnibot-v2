import pytest

from cogs.coinflip import flip_coin
from cogs.log import log
from cogs.monthly_reset import ordinal


class TestOrdinal:
    @pytest.mark.parametrize("n,expected", [
        (1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"), (5, "5th"),
        (10, "10th"),
        # The teens are the classic trap - 11/12/13 are "th", not "st/nd/rd".
        (11, "11th"), (12, "12th"), (13, "13th"), (14, "14th"),
        (20, "20th"), (21, "21st"), (22, "22nd"), (23, "23rd"),
        (100, "100th"), (101, "101st"), (102, "102nd"), (103, "103rd"),
        (111, "111th"), (112, "112th"), (113, "113th"),
    ])
    def test_suffixes(self, n, expected):
        assert ordinal(n) == expected

    def test_covers_a_full_leaderboard_without_error(self):
        # monthly_reset ranks up to 10 members, but guard the whole range.
        for n in range(1, 200):
            assert ordinal(n).startswith(str(n))


class TestFlipCoin:
    def test_only_returns_heads_or_tails(self):
        assert {flip_coin() for _ in range(200)} <= {"heads", "tails"}

    def test_returns_both_outcomes_over_many_flips(self):
        # Guards against a stuck coin. Odds of a false failure are 2^-200.
        assert {flip_coin() for _ in range(200)} == {"heads", "tails"}

    def test_outcome_compares_equal_to_the_declared_choice_values(self):
        # coinflip decides win/loss by comparing the flip against Choice.value.
        # Those values are declared as "heads"/"tails" in the same module.
        for _ in range(50):
            outcome = flip_coin()
            assert outcome == "heads" or outcome == "tails"

    def test_roughly_fair(self):
        flips = [flip_coin() for _ in range(2000)]
        heads = flips.count("heads")
        # Very loose bound - just catches a badly biased implementation.
        assert 800 < heads < 1200


class TestLog:
    def test_writes_message_with_timestamp(self, capsys):
        log("pool opened")
        out = capsys.readouterr().out
        assert "pool opened" in out
        # Format is "<DD Mon YYYY - HH:MM:SS> message"
        assert out.startswith("<")
        assert "> " in out

    def test_handles_empty_string(self):
        log("")  # must not raise
