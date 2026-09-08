#!/usr/bin/env python3
"""Schema and self-certification check for the dispatch queue.

`rules/queue.md` § *QUEUE.md* says every row carries an `ID` and an
`Acceptance`, and that `Acceptance` is a command that exits 0, never prose.
This script is the executable half of that rule.

It enforces a floor, not the ladder. A green run says the queue is
well-formed and that no row certifies itself; it says nothing about whether a
command tests the row's actual claim. That judgment is step 2 of
`skills/prose-to-spec/playbook.md` and no script makes it. Do not read exit 0
as "these acceptances are good".

Two substantive rules here. The first is the origin floor:

    Every row names the session doc it was dispatched from -- the heading its
    entry was cut into, or the doc itself -- and that heading exists.

`prose-to-spec` used to read a bullet and never the prose behind it, and that
prose can veto everything the row does: the entry behind `042 - audit-de-lo-ya-
construido` said the output is checks in `scripts/checks.sh` and never a
findings doc, and no title carries that on its own. Which is why the entry is
cut rather than deleted when the item moves -- the veto has to survive the move
or the field points at nothing. The field does not prove the veto was honoured;
nothing does.
It proves the entry was opened, because the row cannot be written without
naming it, and it is what lets a refusal go back to the item it came from.

Neither file of the pending pair is an origin, and both are refused for the
same reason: the commit that adds the row empties them of the item. The bullet
becomes an `## En curso` line, which carries one clause and no paragraph to
veto with, and the entry is cut out of `BACKLOG.md` and pasted, verbatim and
under its own heading, into the session doc that dispatched the row. That doc
is what `Origin` names, and a row the session decided itself names it bare
(`rules/queue.md` § *QUEUE.md*).

The second is the self-certification floor:

    An acceptance built only out of existence predicates is rejected when any
    path it tests lives inside this repo.

That is the defect this file was written for. `test -f skills/x/playbook.md`
as the acceptance for a row that writes `skills/x/playbook.md` proves that a
file was created by the same session that promised to create it, which is the
one thing nobody needed proved. The same predicate against a path the row does
not write — `test -L ~/.claude/skills/x/SKILL.md`, created by `install.sh` —
is a real assertion about a real side effect, and passes.
"""

import os
import re
import sys
from pathlib import Path

ROW = re.compile(r"^- \[[ x]\] (?:\(@[^)]+\)\s*)?(.+)$")
FIELD = re.compile(r"^\s{2,}- \*\*([A-Za-z ]+)\*\*:\s*(.*)$")
BACKTICKED = re.compile(r"^`([^`]+)`$")

# `BACKLOG.md` § *042 - slug*, or a bare `sessions/2026-01-01-theme.md`.
ORIGIN = re.compile(r"^`([^`]+)`(?:\s+§\s+\*(.+)\*)?$")

# Two files a row cannot point at, both for the same reason: the commit that
# adds the row empties them of the item. The bullet becomes an `## En curso`
# line and the entry is cut into the dispatching session doc, which is what
# `Origin` names instead (`rules/project-docs.md`, section "QUEUE.md").
DEAD_ON_ARRIVAL = {
    "BACKLOG.md": "Origin names `BACKLOG.md`, and the entry it points at is deleted "
    "by the commit that adds this row. Name the session doc the entry was cut into",
    "PENDING.md": "Origin names `PENDING.md`, which carries one clause per item and no "
    "paragraph to veto the row with, and whose bullet this commit rewrites",
}
HEADING = re.compile(r"^#{2,3}\s+(.+?)\s*$")

# `test -f PATH`, `[ -f PATH ]`, with an optional leading `!`.
EXISTENCE = re.compile(r"^!?\s*(?:test\s+-([efdLsrwx])\s+(\S+)|\[\s+-([efdLsrwx])\s+(\S+)\s+\])$")


def inside_repo(path, root):
    """True when the path a predicate tests lands in the linted checkout.

    Resolved, not prefix-matched: `~/repos/agent-rules/skills/x/playbook.md`
    is the same self-certification as `skills/x/playbook.md` and has to be
    caught as one. A glob is treated as inside — an acceptance nobody can run
    literally is not an acceptance.
    """
    expanded = os.path.expandvars(os.path.expanduser(path.strip("\"'")))
    resolved = Path(expanded)
    if not resolved.is_absolute():
        resolved = root / resolved
    return root == resolved or root in resolved.parents


def parse(text):
    """Yield (line number, title, {field: value}) for each row."""
    rows = []
    for lineno, line in enumerate(text.splitlines(), 1):
        row = ROW.match(line)
        if row:
            rows.append((lineno, row.group(1).strip(), {}))
            continue
        field = FIELD.match(line)
        if field and rows:
            rows[-1][2][field.group(1)] = field.group(2).strip()
    return rows


def clauses(command):
    return [c.strip() for c in re.split(r"&&|\|\||;", command) if c.strip()]


def existence_paths(command):
    """Paths tested, if every clause is an existence predicate. Else None."""
    paths = []
    for clause in clauses(command):
        match = EXISTENCE.match(clause)
        if not match:
            return None
        paths.append(match.group(2) or match.group(4))
    return paths


def discover_origins(root):
    """{path: {heading titles}} for every file a row is allowed to name.

    Read from disk, so `lint()` stays pure: `main()` passes the result in and
    the self-test passes fixtures of its own. Only `sessions/` is here, and
    `PENDING.md` and `BACKLOG.md` are absent on purpose; see the origin floor
    in this file's docstring and `DEAD_ON_ARRIVAL` above.
    """
    origins = {}
    sessions = sorted(str(p.relative_to(root)) for p in (root / "sessions").glob("*.md"))
    for path in sessions:
        try:
            text = (root / path).read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        origins[path] = {m.group(1) for m in (HEADING.match(l) for l in text.splitlines()) if m}
    return origins


def lint(text, origins=None, root=None):
    """Errors in the queue. `origins` None checks Origin's shape and not its target."""
    root = Path(root) if root is not None else Path.cwd()
    rows = parse(text)
    errors = []
    ids = {}

    for lineno, title, fields in rows:
        where = f"{lineno}: {title[:60]}"

        origin = fields.get("Origin")
        if not origin:
            errors.append(
                f"{where}\n    no Origin. Name the session doc this row was "
                f"dispatched from (`sessions/<date>-<theme>.md` § *NNN - slug*)"
            )
        else:
            match = ORIGIN.match(origin)
            if not match:
                errors.append(
                    f"{where}\n    Origin is not `<file>` or `<file>` § *<section>*: {origin[:70]}"
                )
            elif origins is not None:
                where_from, section = match.group(1), match.group(2)
                if where_from in DEAD_ON_ARRIVAL:
                    errors.append(f"{where}\n    {DEAD_ON_ARRIVAL[where_from]}")
                elif where_from not in origins:
                    errors.append(f"{where}\n    Origin names no file: '{where_from}'")
                elif section and section not in origins[where_from]:
                    errors.append(
                        f"{where}\n    Origin names no section of {where_from}: '{section}'"
                    )

        row_id = fields.get("ID")
        if not row_id:
            errors.append(f"{where}\n    no ID")
        elif row_id in ids:
            errors.append(f"{where}\n    duplicate ID '{row_id}', first used at line {ids[row_id]}")
        else:
            ids[row_id] = lineno

        acceptance = fields.get("Acceptance")
        if not acceptance:
            errors.append(f"{where}\n    no Acceptance")
            continue

        command = BACKTICKED.match(acceptance)
        if not command:
            errors.append(
                f"{where}\n    Acceptance is not a single backticked command: {acceptance[:70]}"
            )
            continue

        inside = [p for p in (existence_paths(command.group(1)) or []) if inside_repo(p, root)]
        if inside:
            errors.append(
                f"{where}\n    acceptance only checks that files exist, and {', '.join(inside)} "
                f"is written by this row. Test what the row claims, not that it ran"
            )

    known = set(ids)
    for lineno, title, fields in rows:
        for dep in re.split(r",\s*", fields.get("Blocked by", "")):
            dep = dep.strip().strip("`")
            if dep and dep not in known:
                errors.append(f"{lineno}: {title[:60]}\n    Blocked by names no row: '{dep}'")

    return errors


ORIGINS = {
    "sessions/2026-01-01-theme.md": {"Plan", "042 - audit-de-lo-ya-construido"},
}
ORIGIN_LINE = (
    "  - **Origin**: `sessions/2026-01-01-theme.md` § *042 - audit-de-lo-ya-construido*\n"
)

# (name, queue text, expected substring, origins passed to lint)
FIXTURES = [
    (
        "no Origin",
        "- [ ] A row\n  - **ID**: a-row\n  - **Acceptance**: `npm test`\n",
        "no Origin",
        None,
    ),
    (
        "Origin as prose",
        "- [ ] A row\n  - **ID**: a-row\n  - **Origin**: the audit section\n"
        "  - **Acceptance**: `npm test`\n",
        "Origin is not",
        None,
    ),
    (
        "Origin names a file that does not exist",
        "- [ ] A row\n  - **ID**: a-row\n  - **Origin**: `ROADMAP.md`\n"
        "  - **Acceptance**: `npm test`\n",
        "Origin names no file",
        ORIGINS,
    ),
    (
        "Origin names a section that does not exist",
        "- [ ] A row\n  - **ID**: a-row\n"
        "  - **Origin**: `sessions/2026-01-01-theme.md` § *A section nobody wrote*\n"
        "  - **Acceptance**: `npm test`\n",
        "Origin names no section",
        ORIGINS,
    ),
    (
        "BACKLOG.md is not an origin, however real its section was when drafted",
        "- [ ] A row\n  - **ID**: a-row\n"
        "  - **Origin**: `BACKLOG.md` § *042 - audit-de-lo-ya-construido*\n"
        "  - **Acceptance**: `npm test`\n",
        "the entry it points at is deleted",
        ORIGINS,
    ),
    (
        "PENDING.md is not an origin, however real its section is",
        "- [ ] A row\n  - **ID**: a-row\n"
        "  - **Origin**: `PENDING.md` § *Pendientes*\n"
        "  - **Acceptance**: `npm test`\n",
        "carries one clause per item",
        ORIGINS,
    ),
    (
        "a bare PENDING.md is not an origin either",
        "- [ ] A row\n  - **ID**: a-row\n  - **Origin**: `PENDING.md`\n"
        "  - **Acceptance**: `npm test`\n",
        "carries one clause per item",
        ORIGINS,
    ),
    (
        "no ID",
        "- [ ] A row\n" + ORIGIN_LINE + "  - **Acceptance**: `npm test`\n",
        "no ID",
        None,
    ),
    (
        "no Acceptance",
        "- [ ] A row\n  - **ID**: a-row\n" + ORIGIN_LINE,
        "no Acceptance",
        None,
    ),
    (
        "prose acceptance",
        "- [ ] A row\n  - **ID**: a-row\n" + ORIGIN_LINE + "  - **Acceptance**: the tests pass\n",
        "not a single backticked command",
        None,
    ),
    (
        "duplicate ID",
        "- [ ] One\n  - **ID**: dup\n" + ORIGIN_LINE + "  - **Acceptance**: `npm test`\n"
        "- [ ] Two\n  - **ID**: dup\n" + ORIGIN_LINE + "  - **Acceptance**: `npm test`\n",
        "duplicate ID",
        None,
    ),
    (
        "self-certifying acceptance",
        "- [ ] Write the playbook\n  - **ID**: pb\n" + ORIGIN_LINE +
        "  - **Acceptance**: `test -f skills/x/playbook.md`\n",
        "written by this row",
        None,
    ),
    (
        "self-certifying half of a composed acceptance",
        "- [ ] Write and install\n  - **ID**: pb\n" + ORIGIN_LINE +
        "  - **Acceptance**: `test -f skills/x/playbook.md && test -L ~/.claude/skills/x/SKILL.md`\n",
        "written by this row",
        None,
    ),
    (
        "self-certification dressed as an absolute path",
        "- [ ] Write the playbook\n  - **ID**: pb\n" + ORIGIN_LINE +
        "  - **Acceptance**: `test -f ~/repos/agent-rules/skills/x/playbook.md`\n",
        "written by this row",
        None,
    ),
    (
        "Blocked by a row that does not exist",
        "- [ ] A row\n  - **ID**: a-row\n" + ORIGIN_LINE + "  - **Blocked by**: ghost\n"
        "  - **Acceptance**: `npm test`\n",
        "names no row",
        None,
    ),
]

CLEAN = (
    "## P0\n\n"
    "- [ ] Install the skill\n"
    "  - **ID**: install-skill\n" + ORIGIN_LINE +
    "  - **Acceptance**: `test -L ~/.claude/skills/x/SKILL.md`\n\n"
    "- [ ] (@worker) Make the audit pass\n"
    "  - **ID**: audit\n"
    "  - **Origin**: `sessions/2026-01-01-theme.md`\n"
    "  - **Blocked by**: install-skill\n"
    "  - **Acceptance**: `python3 scripts/english-audit.py`\n"
)


def self_test():
    failures = []
    for name, fixture, expected, origins in FIXTURES:
        errors = lint(fixture, origins)
        if not any(expected in e for e in errors):
            failures.append(f"fixture '{name}': expected {expected!r}, got {errors or 'nothing'}")
    if lint(CLEAN, ORIGINS):
        failures.append(f"clean fixture rejected: {lint(CLEAN, ORIGINS)}")
    found = discover_origins(Path(__file__).resolve().parent.parent)
    if not any(k.startswith("sessions/") for k in found):
        failures.append("discover_origins() found no session doc; main() would resolve nothing")
    for name in DEAD_ON_ARRIVAL:
        if name in found:
            failures.append(f"discover_origins() offers {name} as an origin; it is not one")

    for failure in failures:
        print(failure)
    if failures:
        print(f"\n{len(failures)} self-test failure(s).")
        return 1
    print(f"queue-lint self-test: {len(FIXTURES)} rejections and 1 clean queue, all as expected.")
    return 0


def main(argv):
    if "--self-test" in argv:
        return self_test()

    roots = [a for a in argv if not a.startswith("-")] or ["."]
    status = 0
    for arg in roots:
        root = Path(arg).resolve()
        # A repo root, like pending-lint.py takes. A QUEUE.md handed in directly
        # still works, and its parent is the repo the origins resolve against.
        path = root if root.is_file() else root / "QUEUE.md"
        root = path.parent
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue  # No queue is a valid state: QUEUE.md is optional.

        errors = lint(text, discover_origins(root), root)
        for error in errors:
            print(f"{path}:{error}")
        if errors:
            print(f"\n{len(errors)} problem(s) in {path}.")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
