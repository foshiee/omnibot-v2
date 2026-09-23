"""Guards against dereferencing a lookup that legitimately returns None.

welcome.py creates a members row on_member_join and levels.py creates one on a
member's first message, but neither fires for someone who was already in the
guild before the bot arrived, or who joined while it was down. Those members get
None back from query(), and any command that goes straight to result[0] dies with
TypeError: 'NoneType' object is not subscriptable.

discord.utils.get has the same shape: it returns None when nothing matches, so a
role or member looked up by name or id can vanish between months.

The source scans below are the part that actually prevents regressions - the
unit tests just pin the wording.
"""

import ast
from pathlib import Path

import pytest

from cogs.member_utils import no_record_message, NO_RECORD_SELF

COGS_DIR = Path(__file__).resolve().parent.parent / "cogs"

# (file, name) -> why reading it without a None check is safe.
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

    @pytest.mark.parametrize("name", ["Garathnor", "a_b_c", "Zoe", "100"])
    def test_interpolates_any_display_name(self, name):
        assert name in no_record_message(name)


# --------------------------------------------------------------------------
# Source scanning
# --------------------------------------------------------------------------

def _is_query_await(node) -> bool:
    """True for `await query(...)`."""
    if not isinstance(node, ast.Await):
        return False
    call = node.value
    return isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "query"


def _is_utils_get(node) -> bool:
    """True for `discord.utils.get(...)`, which returns None when nothing matches."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    owner = node.func.value
    return node.func.attr == "get" and isinstance(owner, ast.Attribute) and owner.attr == "utils"


def _find_subscript(node, name):
    """First `name[...]` anywhere inside `node`."""
    return next((n for n in ast.walk(node)
                 if isinstance(n, ast.Subscript)
                 and isinstance(n.value, ast.Name)
                 and n.value.id == name), None)


def _find_attribute(node, name):
    """First `name.something` anywhere inside `node`."""
    return next((n for n in ast.walk(node)
                 if isinstance(n, ast.Attribute)
                 and isinstance(n.value, ast.Name)
                 and n.value.id == name), None)


def _tests_against_none(test, name) -> bool:
    """True if `test` compares `name` to None."""
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


def _terminates(body) -> bool:
    """True if this branch cannot fall through to the statements after it."""
    return bool(body) and isinstance(body[-1], (ast.Return, ast.Raise, ast.Continue, ast.Break))


def _walk_chain(node):
    """Yield each (test, body) of an if/elif chain in source order.

    An elif is a nested If inside orelse, so the whole chain is one statement as
    far as the enclosing block is concerned. The final else yields test=None.
    """
    while True:
        yield node.test, node.body
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            node = node.orelse[0]
        else:
            if node.orelse:
                yield None, node.orelse
            return


def _inspect(statement, name, find):
    """Classify one statement with respect to `name`.

    Returns (verdict, node): "finding" with the offending node, "guarded" when
    everything after this statement is safe, or "clear" to keep looking.

    An if/elif chain is walked in order. A branch that tests `name is None`
    protects the branches below it, and protects the statements after the whole
    chain only if it cannot fall through - `elif x is None: log(...)` guards the
    rest of the chain but leaves x possibly-None once the chain ends.
    """
    if not isinstance(statement, ast.If):
        hit = find(statement, name)
        return ("finding", hit) if hit is not None else ("clear", None)

    guarded_in_chain = False
    guards_after = False
    for test, body in _walk_chain(statement):
        if test is not None and _tests_against_none(test, name):
            guarded_in_chain = True
            guards_after = guards_after or _terminates(body)
            continue
        if guarded_in_chain:
            continue
        for part in ([test] if test is not None else []) + list(body):
            hit = find(part, name)
            if hit is not None:
                return "finding", hit
    return ("guarded", None) if guards_after else ("clear", None)


def _unguarded(path, is_source, find):
    """Names assigned from `is_source` and then read via `find` with no None check."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for block in _statement_blocks(tree):
        for index, statement in enumerate(block):
            if not (isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and is_source(statement.value)):
                continue
            name = statement.targets[0].id
            for later in block[index + 1:]:
                verdict, hit = _inspect(later, name, find)
                if verdict == "guarded":
                    break
                if verdict == "finding":
                    yield name, hit
                    break


def _unguarded_subscripts(path):
    for name, hit in _unguarded(path, _is_query_await, _find_subscript):
        yield name, hit.lineno


def _unguarded_lookups(path):
    for name, hit in _unguarded(path, _is_utils_get, _find_attribute):
        yield name, hit.attr, hit.lineno


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


class TestLookupResultsAreGuarded:
    """discord.utils.get returns None when nothing matches.

    monthly_reset runs once a month and looks up the top member, every member on
    the leaderboard, and the Dragonslayer role by name. A member who had left, or
    a renamed role, took down the whole month-end run - including the month_exp
    reset at the end of it.
    """

    def test_no_cog_reads_an_attribute_off_an_unguarded_lookup(self):
        offenders = []
        for path in sorted(COGS_DIR.glob("*.py")):
            for name, attribute, lineno in _unguarded_lookups(path):
                if (path.name, name) in ALLOWED_UNGUARDED:
                    continue
                offenders.append(
                    f"  {path.name}:{lineno}: {name}.{attribute} is read with no `if {name} is None` first")
        assert not offenders, (
            "discord.utils.get returns None when nothing matches, so these raise "
            "AttributeError once the role or member stops existing:\n" + "\n".join(offenders)
        )

    def test_the_scan_detects_an_unguarded_lookup(self, tmp_path):
        source = tmp_path / "bad_lookup.py"
        source.write_text(
            "def f(guild):\n"
            "    role = discord.utils.get(guild.roles, name='Dragonslayer')\n"
            "    return role.name\n",
            encoding="utf-8",
        )
        assert list(_unguarded_lookups(source)) == [("role", "name", 3)]

    def test_the_scan_accepts_a_guarded_lookup(self, tmp_path):
        source = tmp_path / "good_lookup.py"
        source.write_text(
            "def f(guild):\n"
            "    role = discord.utils.get(guild.roles, name='Dragonslayer')\n"
            "    if role is None:\n"
            "        return ''\n"
            "    return role.name\n",
            encoding="utf-8",
        )
        assert list(_unguarded_lookups(source)) == []


class TestChainAwareness:
    """An elif that guards protects the branches below it.

    monthly_reset guards top_role with `elif top_role is None`, several branches
    into a chain. A scan that only recognises a guard as a preceding statement
    reports the later top_role.name as unguarded when it is not.
    """

    def test_a_guarding_elif_protects_later_branches(self, tmp_path):
        source = tmp_path / "chain.py"
        source.write_text(
            "def f(guild, member):\n"
            "    role = discord.utils.get(guild.roles, name='Dragonslayer')\n"
            "    if member is None:\n"
            "        log('gone')\n"
            "    elif role is None:\n"
            "        log('no role')\n"
            "    else:\n"
            "        send(role.name)\n",
            encoding="utf-8",
        )
        assert list(_unguarded_lookups(source)) == []

    def test_a_branch_above_the_guard_is_still_reported(self, tmp_path):
        # The guard only protects what comes after it, so reading role.name in an
        # earlier branch is a real finding even though the chain checks it later.
        source = tmp_path / "chain_bad.py"
        source.write_text(
            "def f(guild, member):\n"
            "    role = discord.utils.get(guild.roles, name='Dragonslayer')\n"
            "    if member is None:\n"
            "        send(role.name)\n"
            "    elif role is None:\n"
            "        log('no role')\n",
            encoding="utf-8",
        )
        assert list(_unguarded_lookups(source)) == [("role", "name", 4)]

    def test_a_non_terminating_guard_does_not_protect_after_the_chain(self, tmp_path):
        # `elif role is None: log(...)` falls through, so role may still be None
        # once the chain ends.
        source = tmp_path / "fallthrough.py"
        source.write_text(
            "def f(guild, member):\n"
            "    role = discord.utils.get(guild.roles, name='Dragonslayer')\n"
            "    if member is None:\n"
            "        log('gone')\n"
            "    elif role is None:\n"
            "        log('no role')\n"
            "    send(role.name)\n",
            encoding="utf-8",
        )
        assert list(_unguarded_lookups(source)) == [("role", "name", 7)]
