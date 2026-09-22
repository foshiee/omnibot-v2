from datetime import datetime, timedelta

import pytest

from cogs.cooldown_utils import on_cooldown, format_remaining

NOW = datetime(2026, 1, 15, 12, 0, 0)
DELTA = timedelta(hours=22)


class TestOnCooldown:
    def test_no_previous_use_is_not_on_cooldown(self):
        # A member who has never used the command must always be allowed.
        assert on_cooldown(None, NOW, DELTA) is False

    def test_just_used_is_on_cooldown(self):
        assert on_cooldown(NOW, NOW, DELTA) is True

    def test_within_window_is_on_cooldown(self):
        last = NOW - timedelta(hours=21, minutes=59)
        assert on_cooldown(last, NOW, DELTA) is True

    def test_exactly_at_window_is_still_on_cooldown(self):
        # last + delta == now, and the check is "sum < now", so this is a boundary.
        last = NOW - DELTA
        assert on_cooldown(last, NOW, DELTA) is True

    def test_past_window_is_not_on_cooldown(self):
        last = NOW - timedelta(hours=22, seconds=1)
        assert on_cooldown(last, NOW, DELTA) is False

    def test_long_past_is_not_on_cooldown(self):
        last = NOW - timedelta(days=30)
        assert on_cooldown(last, NOW, DELTA) is False

    @pytest.mark.parametrize("hours,expected", [(0, True), (10, True), (22, True), (23, False), (48, False)])
    def test_window_boundaries(self, hours, expected):
        last = NOW - timedelta(hours=hours)
        assert on_cooldown(last, NOW, DELTA) is expected

    def test_returns_real_booleans(self):
        # Callers branch on this directly, so it must not leak truthy non-bools.
        assert isinstance(on_cooldown(None, NOW, DELTA), bool)
        assert isinstance(on_cooldown(NOW, NOW, DELTA), bool)


class TestFormatRemaining:
    """The cogs each inline their own hours/minutes/seconds ladder.

    Those use `> 3600` and `3600 > x > 60`, so exactly 60 or 3600 seconds falls
    through every branch. These boundaries are the point of the shared helper.
    """

    @pytest.mark.parametrize("seconds,expected", [
        (0, "0 seconds"),
        (1, "1 second"),
        (2, "2 seconds"),
        (59, "59 seconds"),
        (60, "1 minute"),
        (90, "2 minutes"),
        (3599, "60 minutes"),
        (3600, "1 hour"),
        (7200, "2 hours"),
        (79200, "22 hours"),
    ])
    def test_known_durations(self, seconds, expected):
        assert format_remaining(seconds) == expected

    def test_never_reports_a_negative(self):
        # A clock skew or a stale row can put the deadline in the past.
        assert format_remaining(-5) == "0 seconds"

    def test_singular_and_plural_agree(self):
        assert format_remaining(1) == "1 second"
        assert format_remaining(60) == "1 minute"
        assert format_remaining(3600) == "1 hour"
