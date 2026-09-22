"""Guards against reading a members row that was never created.

welcome.py creates a row on_member_join and levels.py creates one on a member's
first message, but neither fires for someone who was already in the guild before
the bot arrived, or who joined while it was down. Those members get None back
from query(), and any command that goes straight to result[0] dies with
TypeError: 'NoneType' object is not subscriptable.

The source scan below is the part that actually prevents regressions - the unit
tests just pin the wording.
"""

import ast
from pathlib import Path

import pytest

from cogs.member_utils import no_record_message, NO_RECORD_SELF

COGS_DIR = Path(__file__).resolve().parent.parent / "cogs"

# name -> why subscripting it without a None check is safe.
ALLOWED_UNGUARDED = {
    ("dbutils.py", "result"): "SELECT COUNT(*) always returns exactly one row",
    ("welcome.py", "result"): "SELECT COUNT(*) always returns exactly one row",
}


class TestNoRecordMessage:
    def test_names_the_other_member(self):
        message = no_record_message("Garathnor")
        assert "Garathnor" in message
        assert "Have they spoken in this server before?" in message

    def test_addresses_the_caller_directly_when_no_name_is_given(self):
        # "Have they spoken here before?" reads oddly aimed at the person asking.
        message = no_record_message()
        assert message == NO_RECORD_SELF
        assert "they" not in message.lower()
        assert "you" in message.lower()

    def test_both_forms_are_recognisable_as_the_same_problem(self):
        assert no_record_message().startswith(":question:")
        assert no_record_message("Garathnor").startswith(":question:")

    @pytest.mark.parametrize("name", ["Garathnor", "a_b_c", "Ünïcødé", "100"])
    def test_interpolates_any_display_name(self, name):
        assert name in no_record_message(name)


def _is_query_await(node) -> bool:
    """True for `await query(...)`."""
    if not isinstance(node, ast.Await):
        return False
    call = node.value
    return isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "query"


def _tests_against_none(test, name) -> bool:
    """True if `test` compares `name` to None anywhere within it."""
    for node in ast.walk(test):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == name:
            if any(isinstance(c, ast.Constant) and c.value is None for c in node.comparators):
                return True
    return False


def _statement_blocks(tree):
    """Every list-of-statements in the tree.

    if/try bodies live in orelse and finalbody as well as body; walking only
    `body` silently skips every else branch, which is exactly where half of
    these queries are.
    """
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list) and block and all(isinstance(s, ast.stmt) for s in block):
                yield block


def _unguarded_subscripts(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for block in _statement_blocks(tree):
        for index, statement in enumerate(block):
            if not (isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and _is_query_await(statement.value)):
                continue
            name = statement.targets[0].id
            # Walk forward through the same block: the first None check clears
            # the name, the first subscript before one is a finding.
            for later in block[index + 1:]:
                if isinstance(later, ast.If) and _tests_against_none(later.test, name):
                    break
                subscript = next(
                    (n for n in ast.walk(later)
                     if isinstance(n, ast.Subscript)
                     and isinstance(n.value, ast.Name)
                     and n.value.id == name),
                    None,
                )
                if subscript is not None:
                    yield name, subscript.lineno
                    break


class TestQueryResultsAreGuarded:
    def test_no_cog_subscripts_a_query_result_without_a_none_check(self):
        offenders = []
        for path in sorted(COGS_DIR.glob("*.py")):
            for name, lineno in _unguarded_subscripts(path):
                if (path.name, name) in ALLOWED_UNGUARDED:
                    continue
                offenders.append(f"  {path.name}:{lineno}: {name}[...] is read with no `if {name} is None` first")
        assert not offenders, (
            "query() returns None when the member has no row yet, so these raise "
            "TypeError for anyone who has not posted - guard them with "
            "send_no_record() from cogs.member_utils:\n" + "\n".join(offenders)
        )

    def test_the_scan_detects_an_unguarded_read(self, tmp_path):
        # A guard test that cannot fail is worse than no test, so prove this one
        # catches the exact shape it is meant to catch.
        source = tmp_path / "bad.py"
        source.write_text(
            "async def f():\n"
            "    result = await query(returntype='one', sql='SELECT coins FROM members')\n"
            "    coins = result[0]\n",
            encoding="utf-8",
        )
        assert list(_unguarded_subscripts(source)) == [("result", 3)]

    def test_the_scan_accepts_a_guarded_read(self, tmp_path):
        source = tmp_path / "good.py"
        source.write_text(
            "async def f():\n"
            "    result = await query(returntype='one', sql='SELECT coins FROM members')\n"
            "    if result is None:\n"
            "        return\n"
            "    coins = result[0]\n",
            encoding="utf-8",
        )
        assert list(_unguarded_subscripts(source)) == []

    def test_the_scan_looks_inside_else_branches(self, tmp_path):
        # rep.py and cookies.py both query the caller's own row inside an else,
        # which an orelse-blind scan would never see.
        source = tmp_path / "else_branch.py"
        source.write_text(
            "async def f():\n"
            "    if cond:\n"
            "        pass\n"
            "    else:\n"
            "        other = await query(returntype='one', sql='SELECT rep FROM members')\n"
            "        rep = other[0]\n",
            encoding="utf-8",
        )
        assert list(_unguarded_subscripts(source)) == [("other", 6)]
