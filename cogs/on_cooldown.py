def on_cooldown(last_time, new_time, delta) -> bool:
    if last_time is None:
        return False
    else:
        time_sum = last_time + delta
        if time_sum < new_time:
            return False
    return True
