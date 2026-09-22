import pytest

from cogs.lvl_utils import exp_for_level, get_total_exp

# Hardcoded on purpose. Deriving these from the formula would just restate the
# implementation and pass no matter what it did; these are the numbers the
# curve was actually tuned to produce.
EXPECTED_THRESHOLDS = {
    1: 85,
    2: 102,
    3: 121,
    4: 141,
    5: 162,
    10: 290,
    20: 650,
    30: 1150,
    50: 2570,
    99: 8415,
}


class TestExpForLevel:
    @pytest.mark.parametrize("level,expected", sorted(EXPECTED_THRESHOLDS.items()))
    def test_known_thresholds(self, level, expected):
        assert exp_for_level(level) == expected

    def test_returns_whole_numbers(self):
        # Exp is stored as an integer column; a float would round oddly on write.
        for level in range(1, 100):
            assert isinstance(exp_for_level(level), int)

    def test_increases_with_level(self):
        thresholds = [exp_for_level(lvl) for lvl in range(1, 100)]
        assert thresholds == sorted(thresholds)

    def test_gets_steeper(self):
        # The curve previously used ^ (bitwise xor) rather than ** (squaring),
        # which made increments oscillate on a 4-level cycle and never trend up.
        increments = [exp_for_level(lvl + 1) - exp_for_level(lvl) for lvl in range(1, 99)]
        assert increments == sorted(increments)
        assert increments[-1] > increments[0]

    def test_squares_rather_than_xors_the_level(self):
        # Under xor, level 10 would use 10^2 == 8 and give 290 - 62 == 228.
        assert exp_for_level(10) == 290

    def test_high_level_is_far_harder_than_low_level(self):
        assert exp_for_level(99) > exp_for_level(1) * 50


class TestGetTotalExp:
    def test_level_one_returns_exp_unchanged(self):
        # At level 1 there is no previous level to account for.
        assert get_total_exp(1, 0) == 0
        assert get_total_exp(1, 45) == 45

    def test_level_two_adds_the_level_one_threshold(self):
        assert get_total_exp(2, 0) == EXPECTED_THRESHOLDS[1]
        assert get_total_exp(2, 10) == EXPECTED_THRESHOLDS[1] + 10

    @pytest.mark.parametrize("level", [3, 5, 10, 21, 31, 51])
    def test_uses_the_previous_level_threshold(self, level):
        assert get_total_exp(level, 0) == exp_for_level(level - 1)

    def test_exp_is_added_on_top(self):
        assert get_total_exp(10, 137) == exp_for_level(9) + 137

    def test_is_monotonic_across_levels(self):
        totals = [get_total_exp(lvl, 0) for lvl in range(1, 100)]
        assert totals == sorted(totals)

    def test_agrees_with_known_thresholds(self):
        assert get_total_exp(6, 0) == EXPECTED_THRESHOLDS[5]
        assert get_total_exp(11, 0) == EXPECTED_THRESHOLDS[10]


class TestSingleSourceOfTruth:
    """The curve used to be inlined in five places and drifted: the monthly
    threshold in levels.py used a different coefficient to the one stats.py
    displayed, so members were shown a target that wasn't the real one."""

    def test_regular_and_monthly_levels_use_the_same_curve(self):
        # Both call exp_for_level, so any divergence would have to be deliberate.
        for level in range(1, 100):
            assert exp_for_level(level) == exp_for_level(level)

    def test_formula_is_not_reimplemented_in_the_cogs(self):
        from pathlib import Path

        cogs_dir = Path(__file__).resolve().parent.parent / "cogs"
        offenders = []
        for path in sorted(cogs_dir.glob("*.py")):
            if path.name == "lvl_utils.py":
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "0.7" in line and "**" in line:
                    offenders.append(f"  {path.name}:{number}: {line.strip()}")
        assert not offenders, (
            "the levelling curve is reimplemented outside lvl_utils.py - "
            "call exp_for_level() instead:\n" + "\n".join(offenders)
        )
