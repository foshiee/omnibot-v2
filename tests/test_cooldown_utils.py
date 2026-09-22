from datetime import datetime, timedelta

import pytest

from cogs.cooldown_utils import on_cooldown, format_remaining
from cogs.omnicoins import DAILY_DELTA, STREAK_DELTA

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
    """Boundaries are the point of this helper.

    The inline ladders it replaced used `> 3600` and `3600 > x > 60`, so exactly
    60 or exactly 3600 seconds fell through every branch and the embed rendered
    an empty ":hourglass:" field.
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


class TestDailyStreakWindow:
    """The daily cooldown and the streak window are only meaningful together.

    The claim opens at DAILY_DELTA and the streak survives until STREAK_DELTA,
    so the window to keep a streak is whatever sits between them. They were 22h
    and 24h, leaving a 2 hour window - miss it by a minute and the streak reset.
    """

    def test_the_streak_outlives_the_cooldown(self):
        # If these ever crossed, the claim would only unlock after the streak had
        # already lapsed and no streak could be kept at all.
        assert STREAK_DELTA > DAILY_DELTA

    def test_the_window_is_the_advertised_fourteen_hours(self):
        assert DAILY_DELTA == timedelta(hours=22)
        assert STREAK_DELTA == timedelta(hours=36)
        assert STREAK_DELTA - DAILY_DELTA == timedelta(hours=14)

    def test_the_boundary_instant_is_still_on_cooldown(self):
        # on_cooldown uses `last + delta < now`, so the claim unlocks a moment
        # after DAILY_DELTA rather than exactly on it. Shared with cookies and
        # rep, and immaterial at this scale, but worth pinning down.
        last = datetime(2026, 9, 23, 20, 0)
        assert on_cooldown(last, last + DAILY_DELTA, DAILY_DELTA)
        assert not on_cooldown(last, last + DAILY_DELTA + timedelta(seconds=1), DAILY_DELTA)

    def test_claiming_at_the_earliest_moment_keeps_the_streak(self):
        last = datetime(2026, 9, 23, 20, 0)
        earliest = last + DAILY_DELTA + timedelta(seconds=1)
        assert not on_cooldown(last, earliest, DAILY_DELTA)
        assert last + STREAK_DELTA > earliest

    def test_claiming_a_full_extra_half_day_late_still_keeps_the_streak(self):
        last = datetime(2026, 9, 23, 20, 0)
        # The evening after the one they meant to claim on.
        late = last + timedelta(hours=35)
        assert not on_cooldown(last, late, DAILY_DELTA)
        assert last + STREAK_DELTA > late

    def test_claiming_past_the_window_breaks_the_streak(self):
        last = datetime(2026, 9, 23, 20, 0)
        too_late = last + timedelta(hours=37)
        assert not on_cooldown(last, too_late, DAILY_DELTA)
        assert last + STREAK_DELTA <= too_late
