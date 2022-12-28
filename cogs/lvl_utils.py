import math


def get_total_exp(level, exp):
    if level > 1:
        level -= 1  # subtract 1 for the calculation
        total_exp = math.floor(5 * (level ^ 2) + 30 * level + 100)  # gets exp required for previous level up
        total_exp += exp  # adds experience gained since previous level up
        level += 1  # restore to original value
    else:
        total_exp = exp
    return total_exp
