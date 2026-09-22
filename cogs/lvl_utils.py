import math


def exp_for_level(level):
    """Exp needed to advance from `level` to the next one.

    The single definition of the levelling curve - levels.py uses it to decide
    when someone levels up, stats.py to render how far off the next level they
    are. Keeping one copy is deliberate: these used to be separate inline
    formulas and drifted apart, so the monthly threshold shown to members did
    not match the one actually used to level them up.
    """
    return math.floor(0.7 * (level ** 2) + 15 * level + 70)


def get_total_exp(level, exp):
    if level > 1:
        total_exp = exp_for_level(level - 1)  # exp required for the previous level up
        total_exp += exp  # adds experience gained since previous level up
    else:
        total_exp = exp
    return total_exp
