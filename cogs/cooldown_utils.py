def on_cooldown(last_time, new_time, delta) -> bool:
    if last_time is None:
        return False
    else:
        time_sum = last_time + delta
        if time_sum < new_time:
            return False
    return True


def format_remaining(seconds) -> str:
    """Human-readable time left, e.g. "3 hours", "12 minutes", "1 second".

    The cogs each inline their own hours/minutes/seconds ladder, and those use
    `> 3600` / `3600 > x > 60`, which report nothing at exactly 60 or 3600.
    """
    if seconds >= 3600:
        hours = round(seconds / 3600)
        return f"{hours} hour" + ("" if hours == 1 else "s")
    if seconds >= 60:
        minutes = round(seconds / 60)
        return f"{minutes} minute" + ("" if minutes == 1 else "s")
    whole = max(0, round(seconds))
    return f"{whole} second" + ("" if whole == 1 else "s")
