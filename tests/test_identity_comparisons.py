"""Guards against `is` / `is not` being used for value comparison.

Comparing Discord snowflake IDs with `is` compares object identity, not value.
Equal IDs held by two distinct objects are not the same object (they are far
above CPython's small-int cache), so guards like "you can't cookie yourself"
silently stop working whenever the two objects aren't the same cached instance.

Whether it happens to pass depends on discord.py's member cache, which makes it
environment-dependent - the worst kind of bug to chase. These tests fail on the
pattern itself rather than trying to reproduce the cache conditions.
"""
import ast
from pathlib import Path

import pytest

COGS_DIR = Path(__file__).resolve().parent.parent / "cogs"
COG_FILES = sorted(COGS_DIR.glob("*.py"))

# `x is None`, `x is True`, `x is False` are the legitimate uses of identity.
ALLOWED_LITERALS = (None, True, False)


def _is_allowed_operand(node):
    return isinstance(node, ast.Constant) and any(node.value is lit for lit in ALLOWED_LITERALS)


def find_identity_comparisons(path):
    """Return (line, source) for every `is` / `is not` that isn't against a singleton."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    found = []

    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Compare):
            continue
        for op, comparator in zip(node.ops, node.comparators):
            if not isinstance(op, (ast.Is, ast.IsNot)):
                continue
            left_ok = _is_allowed_operand(node.left)
            right_ok = _is_allowed_operand(comparator)
            if not (left_ok or right_ok):
                found.append((node.lineno, lines[node.lineno - 1].strip()))
    return found


@pytest.mark.parametrize("path", COG_FILES, ids=lambda p: p.name)
def test_no_identity_comparison_on_values(path):
    offenders = find_identity_comparisons(path)
    assert not offenders, (
        f"{path.name} compares values with `is`/`is not` - use == / != instead:\n"
        + "\n".join(f"  line {line}: {src}" for line, src in offenders)
    )


class TestSnowflakeIdentitySemantics:
    """Demonstrates why the above matters, independent of discord.py."""

    def test_equal_snowflake_ids_are_not_the_same_object(self):
        member_id = 186548721045995520
        user_id = int("186548721045995520")
        assert member_id == user_id
        assert (member_id is user_id) is False

    def test_small_ints_pass_by_luck(self):
        # Why the bug can look fine in casual testing: CPython caches -5..256.
        assert (5 is int("5")) is True

    def test_the_detector_flags_a_bad_comparison(self, tmp_path):
        bad = tmp_path / "bad.py"
        bad.write_text("a = 1\nb = 2\nif a is b:\n    pass\n", encoding="utf-8")
        assert find_identity_comparisons(bad)

    def test_the_detector_allows_none_checks(self, tmp_path):
        good = tmp_path / "good.py"
        good.write_text("x = None\nif x is None:\n    pass\nif x is not None:\n    pass\n", encoding="utf-8")
        assert find_identity_comparisons(good) == []
