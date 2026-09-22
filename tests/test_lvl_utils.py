import math

import pytest

from cogs.lvl_utils import get_total_exp


def curve(level):
    """The level-up threshold formula, mirrored here so the tests pin the
    intended curve rather than just re-running whatever the code does."""
    return math.floor(0.7 * (level ** 2) + 15 * level + 70)


class TestGetTotalExp:
    def test_level_one_returns_exp_unchanged(self):
        # At level 1 there is no previous level to account for.
        assert get_total_exp(1, 0) == 0
        assert get_total_exp(1, 45) == 45

    def test_level_two_adds_previous_level_threshold(self):
        # Reaching level 2 means the level 1 threshold was already earned.
        assert get_total_exp(2, 0) == curve(1)
        assert get_total_exp(2, 10) == curve(1) + 10

    @pytest.mark.parametrize("level", [3, 5, 10, 25, 50, 99])
    def test_uses_previous_level_threshold(self, level):
        assert get_total_exp(level, 0) == curve(level - 1)

    def test_exp_is_added_on_top(self):
        assert get_total_exp(10, 137) == curve(9) + 137

    def test_is_monotonic_across_levels(self):
        # Total exp must never go down as level increases.
        totals = [get_total_exp(lvl, 0) for lvl in range(1, 100)]
        assert totals == sorted(totals)

    def test_does_not_mutate_caller_arguments(self):
        # The implementation decrements then restores `level` internally.
        level = 10
        get_total_exp(level, 5)
        assert level == 10


class TestCurveShape:
    """The curve was previously ^ (bitwise xor) instead of ** (squaring), which
    made difficulty flat. These pin the intended quadratic shape."""

    def test_squares_the_level(self):
        # XOR would give level 10 -> 10^2 == 8; squaring gives 100.
        assert curve(10) == math.floor(0.7 * 100 + 150 + 70)

    def test_thresholds_increase_with_level(self):
        thresholds = [curve(lvl) for lvl in range(1, 100)]
        assert thresholds == sorted(thresholds)

    def test_increments_grow_each_level(self):
        # A real curve gets steeper; the old xor version oscillated on a 4-level
        # cycle and never trended upward.
        increments = [curve(lvl + 1) - curve(lvl) for lvl in range(1, 99)]
        assert increments == sorted(increments)
        assert increments[-1] > increments[0]

    def test_high_level_is_much_harder_than_low_level(self):
        assert curve(99) > curve(1) * 50
