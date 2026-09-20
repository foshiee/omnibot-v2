import math


def get_total_exp(level, exp):
    if level > 1:
        level -= 1  # subtract 1 for the calculation
        total_exp = math.floor(0.7 * (level ** 2) + 15 * level + 70)  # gets exp required for previous level up
        total_exp += exp  # adds experience gained since previous level up
        level += 1  # restore to original value
    else:
        total_exp = exp
    return total_exp
