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

The third is the reach floor, and it is the one with a test file in it:

    When the acceptance runs a test file in this repo and the row names
    `Files`, that test has to reach one of them: an import, a `require`, a
    Python `from x import`, or a string literal naming the path.

The case it was written for is a `dadatien` acceptance that rebuilt the
component's label logic inside the test file and passed it to a primitive:
the test failed before the fix, failed for the defect's string, and could not
be moved by any edit to the file the row named, so the run spent its attempts
on a file it could not reach. Reach is a floor too: a test that imports the
artifact and still asserts on its own copy passes it, and a case that pins
the broken state alongside the fixed one is invisible here. Both stay with
`skills/prose-to-spec/playbook.md` § *2. Write the acceptance command, then
run it*.
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


SOURCE_EXT = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".py", ".sh"}
TEST_PATH = re.compile(r"(?:^|/)(?:tests?|__tests__|spec)(?:/|$)|\.(?:test|spec|acceptance)\.")
JS_IMPORT = re.compile(r"""(?:\bfrom\s+|\bimport\s+|\brequire\(\s*|\bimport\(\s*)['"]([^'"]+)['"]""")
PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import\b|import\s+([\w.]+))", re.M)
STRING_PATH = re.compile(r"""['"]([^'"\s]+/[^'"\s]+)['"]""")
ALIAS = re.compile(r"^[@~#]/")

def segments(path):
    """A path as a tuple of segments, extension stripped, `/index` dropped.

    `components/admin-items-table.tsx`, `@/components/admin-items-table` and
    `../../components/admin-items-table` all reduce to the same tuple once the
    alias is stripped and the relative part resolved, which is what lets a
    `Files` entry and an import be compared at all.
    """
    parts = [p for p in path.replace("\\", "/").split("/") if p and p != "."]
    if parts and parts[-1] == "index":
        parts.pop()
    if parts:
        parts[-1] = re.sub(r"\.[A-Za-z0-9]+$", "", parts[-1])
    return tuple(parts)

def row_files(fields):
    """The paths a row's `Files` names, backticked or bare, comma-separated."""
    value = fields.get("Files", "")
    ticked = re.findall(r"`([^`]+)`", value)
    return [f.strip() for f in (ticked or value.split(",")) if f.strip()]

def acceptance_tests(command, root):
    """Repo-relative test files the acceptance command runs, read from disk."""
    found = []
    for token in command.split():
        token = token.strip("\"'")
        if not token or token.startswith("-"):
            continue
        candidate = Path(os.path.expanduser(token))
        if not candidate.is_absolute():
            candidate = root / candidate
        if candidate.suffix not in SOURCE_EXT or not candidate.is_file():
            continue
        if not inside_repo(token, root):
            continue
        rel = str(candidate.resolve().relative_to(root.resolve()))
        if TEST_PATH.search(rel):
            found.append(rel)
    return found

def reaches(test_rel, root):
    """Every path a test file reaches, as segment tuples.

    Imports and requires in JS/TS, `import` and `from` in Python, and any
    string literal with a slash in it, so a test that reads the artifact as
    data (`readFileSync("migrations/0007.sql")`) counts as reaching it.
    A relative specifier resolves against the test's own directory; an alias
    prefix (`@/`, `~/`, `#/`) is dropped, since the comparison is by suffix.
    """
    text = (root / test_rel).read_text(encoding="utf-8", errors="replace")
    specs = JS_IMPORT.findall(text) + STRING_PATH.findall(text)
    specs += [a or b for a, b in PY_IMPORT.findall(text)]
    base = Path(test_rel).parent
    out = set()
    for spec in specs:
        if spec.startswith("."):
            spec = os.path.normpath(str(base / spec))
        elif ALIAS.match(spec):
            spec = ALIAS.sub("", spec)
        elif "/" not in spec and "." in spec and not spec.startswith("node:"):
            spec = spec.replace(".", "/")  # a dotted Python module
        out.add(segments(spec))
    return out

def touched(entry, is_dir, refs):
    """True when any reached path is the entry, or lands inside it.

    A file entry matches by suffix in either direction, because an alias
    hides the leading directories of one side or the other. A directory
    entry matches when its segments appear contiguously in the reference.
    """
    if not entry:
        return True
    n = len(entry)
    for ref in refs:
        if not ref:
            continue
        if is_dir:
            if any(ref[i:i + n] == entry for i in range(len(ref) - n + 1)):
                return True
        else:
            m = min(n, len(ref))
            if entry[-m:] == ref[-m:]:
                return True
    return False

def unreached(fields, command, root):
    """(test, files) when the acceptance runs a test reaching none of `Files`."""
    tests = acceptance_tests(command, root)
    if not tests:
        return None
    files = [f for f in row_files(fields) if segments(f) not in {segments(t) for t in tests}]
    if not files:
        return None
    for test in tests:
        refs = reaches(test, root)
        for entry in files:
            is_dir = entry.endswith("/") or (root / entry).is_dir()
            if touched(segments(entry), is_dir, refs):
                return None
    return tests[0], files

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

        miss = unreached(fields, command.group(1), root)
        if miss:
            test, files = miss
            errors.append(
                f"{where}\n    acceptance runs {test}, and nothing in it reaches a path in Files "
                f"({', '.join(files)}). A test that rebuilds the artifact fails for its own "
                f"reasons and no fix to the artifact moves it; import what the row names"
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


# (name, {relative path: content}, Files field, Acceptance command, rejected?)
# Each runs against a temporary tree, since the reach floor reads the test file.
MOCKED = (
    'import { render } from "react-dom/server";\n'
    'import { PillSwitch } from "@/components/ui/pill-switch";\n'
    'function renderCell(item) { return item.isPublished ? "Publicado" : "No publicado"; }\n'
)
REACH_FIXTURES = [
    (
        "test rebuilds the artifact and imports only a primitive",
        {"tests/acceptance/944.acceptance.ts": MOCKED, "components/admin-items-table.tsx": ""},
        "`components/admin-items-table.tsx`",
        "node --import tsx --test tests/acceptance/944.acceptance.ts",
        True,
    ),
    (
        "test imports the artifact through an alias",
        {"tests/acceptance/944.acceptance.ts": MOCKED + 'import { T } from "@/components/admin-items-table";\n',
         "components/admin-items-table.tsx": ""},
        "`components/admin-items-table.tsx`",
        "node --import tsx --test tests/acceptance/944.acceptance.ts",
        False,
    ),
    (
        "test imports the artifact relatively",
        {"tests/acceptance/944.acceptance.ts": 'import { T } from "../../components/admin-items-table";\n',
         "components/admin-items-table.tsx": ""},
        "`components/admin-items-table.tsx`",
        "node --import tsx --test tests/acceptance/944.acceptance.ts",
        False,
    ),
    (
        "test reads the artifact as data",
        {"tests/acceptance/653.acceptance.ts": 'const sql = readFileSync("migrations/0007.sql", "utf8");\n',
         "migrations/0007.sql": ""},
        "`migrations/0007.sql`",
        "node --test tests/acceptance/653.acceptance.ts",
        False,
    ),
    (
        "test imports a module inside a directory the row names",
        {"tests/test_thing.py": "from lib.things.thing import f\n", "lib/things/thing.py": ""},
        "`lib/things/`",
        "python3 -m pytest tests/test_thing.py",
        False,
    ),
    (
        "python test imports nothing the row names",
        {"tests/test_thing.py": "import json\n\ndef f(): return 1\n", "lib/thing.py": ""},
        "`lib/thing.py`",
        "python3 -m pytest tests/test_thing.py",
        True,
    ),
    (
        "acceptance runs no test file the lint can read",
        {"components/admin-items-table.tsx": ""},
        "`components/admin-items-table.tsx`",
        "npm test",
        False,
    ),
    (
        "Files names only the acceptance itself",
        {"tests/acceptance/944.acceptance.ts": MOCKED},
        "`tests/acceptance/944.acceptance.ts`",
        "node --test tests/acceptance/944.acceptance.ts",
        False,
    ),
    (
        "acceptance is a check script, not a test",
        {"scripts/english-audit.py": "import sys\n", "AGENTS.md": ""},
        "`AGENTS.md`",
        "python3 scripts/english-audit.py",
        False,
    ),
]

def reach_failures():
    import tempfile
    failures = []
    for name, tree, files, command, rejected in REACH_FIXTURES:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel, content in tree.items():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text(content, encoding="utf-8")
            queue = (
                "- [ ] A row\n  - **ID**: a-row\n" + ORIGIN_LINE +
                f"  - **Files**: {files}\n  - **Acceptance**: `{command}`\n"
            )
            errors = [e for e in lint(queue, None, root) if "reaches" in e]
            if rejected and not errors:
                failures.append(f"reach fixture '{name}': expected a rejection, got nothing")
            if not rejected and errors:
                failures.append(f"reach fixture '{name}': expected clean, got {errors}")
    return failures

def self_test():
    failures = reach_failures()
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
    print(
        f"queue-lint self-test: {len(FIXTURES)} rejections, 1 clean queue and "
        f"{len(REACH_FIXTURES)} reach trees, all as expected."
    )
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
