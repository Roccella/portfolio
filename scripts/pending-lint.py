#!/usr/bin/env python3
"""PENDING.md is what a person scans; BACKLOG.md is what an agent works from.

One item lives in both. `PENDING.md` carries the title and one clause, in the
user's language, in priority order. `BACKLOG.md` carries that item's detail, in
English, keyed by the same id. The id is three digits, `[042]`, because a fixed
width is what lets an eye run down the column instead of tracking a ragged left
edge across every line. `BACKLOG.md` names it `## 042 - some-slug`, which is
where the item gets a readable name and where its `Sessions:` line ties it to
the docs in `sessions/`. No path is ever written into PENDING.

Three measurements, all mechanical:

  1. Length, ratcheted. Any bullet or paragraph over PROSE_LIMIT characters is a
     spec wearing a dash: its detail belongs in BACKLOG.md. How many a file is
     still allowed lives in a `<!-- pending-lint: over140=M -->` marker inside the
     file. Going over M fails; coming under it is reported so --ratchet can lower
     it. A marker with no `over140=` field means M is 0.

  2. Nesting, ratcheted the same way, as `deep=D`. templates/pending.md allows a
     bullet and one level under it. A third level is an outline, and an outline is
     BACKLOG.md's job.

  3. Pairing, not ratcheted. When the repo has a BACKLOG.md, every top-level
     bullet in PENDING.md must open with `**[NNN]**` and every id must have exactly
     one `## NNN` in BACKLOG.md, both ways. A repo with no BACKLOG.md is reported
     as unmigrated and the check is skipped, which is how a repo crosses over.

     One section is exempt: `## Notas` (or `## Notes`) holds what the reader
     needs while scanning and what no item owns — a deadline somebody else set,
     an expiry, a number to quote back. It routes nowhere, so its bullets carry
     no id. The cap and the nesting limit still apply to them.

     Ids are picked at random from 001-999 rather than counted up: "the next free
     number" has to read the file to find the maximum, and that read is the race
     between two sessions. Uniqueness is enforced here, so a collision fails a
     commit instead of drifting. A freed id may be reused, but not one still
     visible in the last year of `git log`, or the history conflates two items.

  4. In-flight mirroring, not ratcheted. `## En curso` (or `## In flight`) is the
     one section a bullet can carry its id into without a matching `## NNN` in
     BACKLOG.md, because that entry was deleted in the commit that moved the item
     to QUEUE.md. Every bullet there must instead name a live QUEUE.md row's `ID`
     slug in its text, and every row's slug must be named by exactly one such
     bullet, checked both ways so the two files cannot drift apart in silence.

There is deliberately no cap on how many items PENDING.md may hold. The count of
open items is information about the work, not a defect, and the ratchet this file
used to keep on it turned "I opened a new theme" into a failing build.

Neither check reads the content. A green run says the file is shaped like a
backlog index and says nothing about whether its items are the right items.

This file is vendored: agent-rules carries the canonical copy, each gated repo
carries its own via scripts/pending-wire.sh, and `pending-wire.sh --check`
reports copies that have drifted from the canonical one.

Usage:
  python3 scripts/pending-lint.py                 # lint . (PENDING.md in cwd)
  python3 scripts/pending-lint.py PATH [PATH...]  # lint specific repo roots
  python3 scripts/pending-lint.py --ratchet PATH  # lower (or seed) both baselines
  python3 scripts/pending-lint.py --self-test     # prove the checks reject
"""
import os
import re
import sys

PROSE_LIMIT = 140       # characters in one bullet or paragraph
MAX_DEPTH = 1           # deepest allowed bullet indent level; 0 is top level

MARKER_RE = re.compile(
    r"<!--\s*pending-lint:\s*(?:baseline=\d+\s+)?(?:over(?P<width>140|320)=(?P<over>\d+))?"
    r"(?:\s+deep=(?P<deep>\d+))?\s*-->"
)
MARKER_FMT = "<!-- pending-lint: over140={} deep={} -->"

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
BULLET_RE = re.compile(r"^([-*+]\s+|\d+\.\s+)")
ID_RE = re.compile(r"^[-*+]\s+\*\*\[([0-9]{3})\]\*\*\s")
# `## 042 - some-slug`: the digits are the key, the slug is for whoever reads it.
HEADING_RE = re.compile(r"^##\s+([0-9]{3})\b", re.MULTILINE)

# The landing spot for new items in an empty section carries no detail, so it
# needs no id and no BACKLOG.md entry. `rules/project-docs.md` mandates the
# wording; anything else in an empty section is a real item.
PLACEHOLDERS = {"- Sin pendientes.", "- No pending items."}

# A `## Notas` section holds what the reader needs while scanning and what no
# item owns: a deadline somebody else set, a credential's expiry, a number to
# quote back. It routes nowhere, so its bullets carry no id and pair with
# nothing. Everything else still applies to them — the 140-char cap, the nesting
# limit — because the failure this exempts is "a fact has no home", not "this
# line is too long to bother trimming". Named sections rather than a per-section
# marker: a marker anyone can write is a way out of the pairing, and the pairing
# is the format.
NOTES_SECTIONS = {"notas", "notes"}

# `## En curso` is the one place PENDING.md names work that lives in QUEUE.md.
# Its bullets keep their id and carry no BACKLOG.md entry, because the entry
# was deleted in the commit that added the row. It is not a second home for
# the spec -- the spec is the row -- it is the index staying true about what
# is running. The pairing is against the queue instead of the backlog, and it
# is checked in both directions so it cannot drift in silence.
INFLIGHT_SECTIONS = {"en curso", "in flight"}

# `  - **ID**: some-slug`: a QUEUE.md row's own id, checked against the
# `## En curso` bullets that are supposed to mirror it.
QUEUE_ID_RE = re.compile(r"^\s*-\s+\*\*ID\*\*:\s*(\S.*)$", re.MULTILINE)


def blocks(text):
    """Yield (kind, first_line_no, text, depth, section) per bullet and paragraph.

    A bullet runs from its marker to the next marker, blank line or heading, so a
    wrapped bullet is measured whole rather than per physical line. `depth` is the
    bullet's nesting level, 0 for top level, and None for a paragraph. Indent is
    read as a stack of widths, so 2-space and 4-space files both come out right.
    `section` is the nearest preceding `##` heading, lowercased and stripped, or
    "" above the first one; only the pairing check reads it.
    """
    lines = text.splitlines()
    buf, start, kind, depth, held = [], 0, None, None, ""
    section = ""
    fenced = False
    commented = False
    stack = []

    def flush():
        nonlocal buf, kind, depth
        out = None
        if buf and kind:
            joined = " ".join(l.strip() for l in buf).strip()
            if joined:
                out = (kind, start + 1, joined, depth, held)
        buf, kind, depth = [], None, None
        return out

    for i, line in enumerate(lines):
        # A comment block is instructions, not backlog, and its interior lines
        # are not paragraphs. Tracked like a fence: the old code only skipped the
        # lines that opened or closed one, so a multi-line header joined into a
        # paragraph and failed the cap.
        if commented:
            if "-->" in line:
                commented = False
            continue
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out = flush()
            if out:
                yield out
            continue
        if fenced:
            continue
        stripped = line.strip()
        is_bullet = bool(BULLET_RE.match(stripped))
        is_heading = stripped.startswith("#")
        is_table = stripped.startswith("|")
        is_comment = stripped.startswith("<!--") or stripped.startswith("-->")
        if is_comment and "<!--" in line and "-->" not in line.split("<!--", 1)[1]:
            commented = True

        if not stripped or is_heading or is_table or is_comment:
            out = flush()
            if out:
                yield out
            if is_heading:
                # Only `##` names a section; `###` and deeper sit inside the one
                # already open, so they must not clear it.
                if re.match(r"^##(?!#)", stripped):
                    section = stripped.lstrip("#").strip().lower()
            if not stripped or is_heading:
                stack = []
            continue
        if is_bullet:
            out = flush()
            if out:
                yield out
            indent = len(line) - len(line.lstrip())
            while stack and stack[-1] > indent:
                stack.pop()
            if not stack or stack[-1] < indent:
                stack.append(indent)
            buf, start, kind, depth, held = [stripped], i, "bullet", len(stack) - 1, section
            continue
        if kind:
            buf.append(stripped)
        else:
            buf, start, kind, depth, held = [stripped], i, "paragraph", None, section

    out = flush()
    if out:
        yield out


def long_blocks(text):
    """Every bullet or paragraph over PROSE_LIMIT, as (lineno, kind, length, head)."""
    return [
        (lineno, kind, len(body), body[:70])
        for kind, lineno, body, _, _section in blocks(text)
        if len(body) > PROSE_LIMIT
    ]


def deep_blocks(text):
    """Every bullet nested past MAX_DEPTH, as (lineno, depth, head)."""
    return [
        (lineno, depth, body[:70])
        for kind, lineno, body, depth, _section in blocks(text)
        if kind == "bullet" and depth is not None and depth > MAX_DEPTH
    ]


def pending_ids(text):
    """(ids, unkeyed) over top-level bullets: the ids found, and the ones missing.

    `unkeyed` is (lineno, head) per top-level bullet with no `**[id]**` opener.
    Placeholders and anything under a NOTES_SECTIONS or INFLIGHT_SECTIONS
    heading are neither: an in-flight bullet's detail lives in the QUEUE.md
    row, not in BACKLOG.md, so it is checked by check_inflight instead.
    """
    ids, unkeyed = [], []
    for kind, lineno, body, depth, section in blocks(text):
        if kind != "bullet" or depth != 0 or body in PLACEHOLDERS:
            continue
        if section in NOTES_SECTIONS or section in INFLIGHT_SECTIONS:
            continue
        found = ID_RE.match(body)
        if found:
            ids.append((found.group(1), lineno))
        else:
            unkeyed.append((lineno, body[:70]))
    return ids, unkeyed


def backlog_ids(text):
    """Every `## id` heading in BACKLOG.md, in order."""
    return HEADING_RE.findall(text)


def inflight_bullets(text):
    """(id_or_None, lineno, body) per top-level bullet under an INFLIGHT_SECTIONS heading."""
    out = []
    for kind, lineno, body, depth, section in blocks(text):
        if kind != "bullet" or depth != 0 or body in PLACEHOLDERS:
            continue
        if section not in INFLIGHT_SECTIONS:
            continue
        found = ID_RE.match(body)
        out.append((found.group(1) if found else None, lineno, body))
    return out


def queue_row_ids(text):
    """Every row `ID` in a QUEUE.md, as a list of slugs. A template placeholder is not one."""
    return [m for m in QUEUE_ID_RE.findall(text) if not (m.startswith("[") and m.endswith("]"))]


def check_pairing(name, pending_text, backlog_path, failures, notices):
    if not os.path.exists(backlog_path):
        notices.append(
            f"{name}: no BACKLOG.md, pairing not checked. "
            f"Detail for these items has no home yet"
        )
        return
    ids, unkeyed = pending_ids(pending_text)
    for lineno, head in unkeyed:
        failures.append(
            f"{name}/PENDING.md:{lineno}: bullet has no `**[NNN]**` id: {head}..."
        )
    seen = {}
    for pid, lineno in ids:
        if pid in seen:
            failures.append(
                f"{name}/PENDING.md:{lineno}: id `{pid}` already used at line {seen[pid]}"
            )
        seen[pid] = lineno

    back = backlog_ids(open(backlog_path, encoding="utf-8").read())
    dupes = {b for b in back if back.count(b) > 1}
    for d in sorted(dupes):
        failures.append(f"{name}/BACKLOG.md: `## {d}` appears more than once")

    only_pending = [p for p in seen if p not in back]
    only_backlog = [b for b in dict.fromkeys(back) if b not in seen]
    for p in sorted(only_pending):
        failures.append(
            f"{name}/PENDING.md:{seen[p]}: `[{p}]` has no `## {p}` in BACKLOG.md"
        )
    for b in sorted(only_backlog):
        failures.append(
            f"{name}/BACKLOG.md: `## {b}` has no bullet in PENDING.md. "
            f"Delete it, or the item was closed on one side only"
        )


def check_inflight(name, pending_text, backlog_text, queue_path, failures, notices):
    rows = queue_row_ids(open(queue_path, encoding="utf-8").read()) if os.path.exists(queue_path) else []
    bullets = inflight_bullets(pending_text)

    if rows and not bullets:
        failures.append(
            f"{name}/PENDING.md: QUEUE.md has {len(rows)} row(s) and no "
            f"`## En curso` section mirrors them"
        )
        return

    back = set(backlog_ids(backlog_text))
    by_slug = {}
    for pid, lineno, body in bullets:
        if pid is None:
            failures.append(
                f"{name}/PENDING.md:{lineno}: `## En curso` bullet has no `**[NNN]**` id: {body[:70]}..."
            )
            continue
        if pid in back:
            failures.append(
                f"{name}/PENDING.md:{lineno}: `[{pid}]` still has `## {pid}` in BACKLOG.md, but the "
                f"entry is deleted in the commit that adds the row, so the item has two homes"
            )
        if len(re.findall(r"\*\*\[" + re.escape(pid) + r"\]\*\*", pending_text)) > 1:
            failures.append(
                f"{name}/PENDING.md:{lineno}: id `{pid}` also appears elsewhere in PENDING.md"
            )
        found_row = next((r for r in rows if r in body), None)
        if found_row is None:
            failures.append(
                f"{name}/PENDING.md:{lineno}: `## En curso` bullet names no QUEUE.md row id, "
                f"so it is not in flight -- it belongs in a theme section with its BACKLOG.md entry"
            )
            continue
        by_slug.setdefault(found_row, []).append(lineno)

    for row in rows:
        linenos = by_slug.get(row, [])
        if not linenos:
            failures.append(f"{name}/PENDING.md: QUEUE.md row `{row}` has no `## En curso` bullet")
        elif len(linenos) > 1:
            failures.append(
                f"{name}/PENDING.md: QUEUE.md row `{row}` is named by more than one `## En curso` "
                f"bullet, at lines {', '.join(str(l) for l in linenos)}"
            )


def check(repo_root, failures, notices):
    name = os.path.basename(os.path.abspath(repo_root))
    path = os.path.join(repo_root, "PENDING.md")
    if not os.path.exists(path):
        return
    text = open(path, encoding="utf-8").read()

    long = long_blocks(text)
    deep = deep_blocks(text)

    found = MARKER_RE.search(text)
    if not found:
        notices.append(
            f"{name}: no pending-lint marker, PENDING.md has {len(long)} block(s) "
            f"over {PROSE_LIMIT} chars and {len(deep)} bullet(s) past level {MAX_DEPTH}. "
            f"Seed it with `pending-lint.py --ratchet {repo_root}`"
        )
        return

    if found.group("width") == "320":
        notices.append(
            f"{name}: the marker still counts against the retired 320-char limit, so its "
            f"number says nothing about {PROSE_LIMIT}. PENDING.md has {len(long)} block(s) "
            f"over {PROSE_LIMIT} chars and {len(deep)} bullet(s) past level {MAX_DEPTH}. "
            f"Reseed it with `pending-lint.py --ratchet {repo_root}`"
        )
        return

    over_cap = int(found.group("over")) if found.group("over") is not None else 0
    deep_cap = int(found.group("deep")) if found.group("deep") is not None else 0

    if len(long) > over_cap:
        failures.append(
            f"{name}/PENDING.md has {len(long)} block(s) over {PROSE_LIMIT} chars, "
            f"over its baseline of {over_cap}. Move the detail to BACKLOG.md:"
        )
        for lineno, kind, length, head in long:
            failures.append(f"    {name}/PENDING.md:{lineno}: {kind}, {length} chars: {head}...")
    elif len(long) < over_cap:
        notices.append(
            f"{name}: ratchet available, {len(long)} block(s) over {PROSE_LIMIT} chars "
            f"(baseline {over_cap})"
        )

    if len(deep) > deep_cap:
        failures.append(
            f"{name}/PENDING.md has {len(deep)} bullet(s) nested past level {MAX_DEPTH}, "
            f"over its baseline of {deep_cap}. An outline belongs in BACKLOG.md:"
        )
        for lineno, depth, head in deep:
            failures.append(f"    {name}/PENDING.md:{lineno}: level {depth}: {head}...")
    elif len(deep) < deep_cap:
        notices.append(
            f"{name}: ratchet available, {len(deep)} bullet(s) past level {MAX_DEPTH} "
            f"(baseline {deep_cap})"
        )

    backlog_path = os.path.join(repo_root, "BACKLOG.md")
    check_pairing(name, text, backlog_path, failures, notices)
    backlog_text = open(backlog_path, encoding="utf-8").read() if os.path.exists(backlog_path) else ""
    check_inflight(name, text, backlog_text, os.path.join(repo_root, "QUEUE.md"), failures, notices)


def ratchet(repo_root):
    name = os.path.basename(os.path.abspath(repo_root))
    path = os.path.join(repo_root, "PENDING.md")
    if not os.path.exists(path):
        print(f"  {name}: no PENDING.md at {repo_root}")
        return 1

    text = open(path, encoding="utf-8").read()
    over = len(long_blocks(text))
    deep = len(deep_blocks(text))
    found = MARKER_RE.search(text)

    if not found:
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("# "):
                insert_at = i + 1
                break
        marker_line = MARKER_FMT.format(over, deep) + "\n"
        if insert_at:
            marker_line = "\n" + marker_line
        lines.insert(insert_at, marker_line)
        open(path, "w", encoding="utf-8").write("".join(lines))
        print(f"  {name}: baselines seeded at {over} long block(s), {deep} deep bullet(s)")
        return 0

    # A `over320=` marker was measured against the retired 320-char limit, so carrying
    # its number into `over140=` seeds a baseline the file never met. Treat it as unseeded:
    # the ratchet only ever lowers, and a number that low blocks every commit in the repo.
    legacy = found.group("width") == "320"
    had_over = found.group("over") is not None and not legacy
    had_deep = found.group("deep") is not None
    over_cap = int(found.group("over")) if had_over else 0
    deep_cap = int(found.group("deep")) if had_deep else 0
    new_over = min(over_cap, over) if had_over else over
    new_deep = min(deep_cap, deep) if had_deep else deep

    if (new_over, new_deep) == (over_cap, deep_cap) and had_over and had_deep:
        print(f"  {name}: baselines stay at {over_cap} long / {deep_cap} deep. They only go down.")
        return 0

    new_text = MARKER_RE.sub(MARKER_FMT.format(new_over, new_deep), text, count=1)
    open(path, "w", encoding="utf-8").write(new_text)
    print(f"  {name}: baselines {over_cap}/{deep_cap} -> {new_over}/{new_deep} (long/deep)")
    return 0


LONG = "- " + ("word " * 40) + "\n"   # one bullet well over PROSE_LIMIT

SELF_TEST_CASES = [
    ("bullet grown into a spec", "# P\n\n## T\n\n" + LONG, True),
    ("free paragraph", "# P\n\n## T\n\n" + ("word " * 40) + "\n", True),
    ("short bullets", "# P\n\n## T\n\n- Do the thing\n- Do the other thing\n", False),
    ("wrapped short bullet", "# P\n\n## T\n\n- Do the thing\n  and its detail\n", False),
    ("long fenced code is exempt", "# P\n\n## T\n\n```\n" + ("x" * 500) + "\n```\n", False),
    ("long table row is exempt", "# P\n\n## T\n\n| " + ("y" * 500) + " |\n", False),
]

COMMENT_TEST_CASES = [
    ("single-line comment is not a paragraph", "<!-- " + ("x" * 400) + " -->\n", False),
    ("multiline comment is not a paragraph",
     "<!--\n" + ("word " * 40) + "\n" + ("word " * 40) + "\n-->\n", False),
    ("text after a comment block is still measured",
     "<!--\nnote\n-->\n\n" + ("word " * 40) + "\n", True),
]

DEPTH_TEST_CASES = [
    ("top level only", "# P\n\n## T\n\n- a\n- b\n", 0),
    ("one level under, 2-space", "# P\n\n## T\n\n- a\n  - b\n", 1),
    ("one level under, 4-space", "# P\n\n## T\n\n- a\n    - b\n", 1),
    ("two levels under, 2-space", "# P\n\n## T\n\n- a\n  - b\n    - c\n", 2),
    ("two levels under, 4-space", "# P\n\n## T\n\n- a\n    - b\n        - c\n", 2),
    ("depth resets after a heading", "# P\n\n## T\n\n  - a\n\n## U\n\n- b\n", 0),
]

# (label, marker, body, expect_failure). The marker is what the ratchet wrote last time.
MARKER_TEST_CASES = [
    ("over the long-block baseline fails",
     "<!-- pending-lint: over140=1 -->", LONG + "\n" + LONG, True),
    ("at the long-block baseline passes",
     "<!-- pending-lint: over140=2 -->", LONG + "\n" + LONG, False),
    ("under the long-block baseline passes",
     "<!-- pending-lint: over140=3 -->", LONG + "\n" + LONG, False),
    ("a marker with no over140 field means zero",
     "<!-- pending-lint: -->", LONG, True),
    ("a marker with no over140 field and no long block passes",
     "<!-- pending-lint: -->", "- short\n", False),
    ("a retired over320= marker is not read as a baseline at all",
     "<!-- pending-lint: baseline=1 over320=1 -->", LONG, False),
    ("a retired over320= marker never fails, however far over its number the file is",
     "<!-- pending-lint: baseline=1 over320=1 -->", LONG + "\n" + LONG + "\n" + LONG, False),
    ("a third bullet level fails",
     "<!-- pending-lint: over140=0 deep=0 -->", "- a\n  - b\n    - c\n", True),
    ("a third bullet level at its baseline passes",
     "<!-- pending-lint: over140=0 deep=1 -->", "- a\n  - b\n    - c\n", False),
]

# (label, starting marker, body, the over140 the ratchet must write)
RATCHET_TEST_CASES = [
    ("a retired over320= marker reseeds at the real 140-char count, it does not carry its number",
     "<!-- pending-lint: baseline=1 over320=1 -->", LONG + "\n" + LONG + "\n" + LONG, 3),
    ("an over140= marker still only goes down",
     "<!-- pending-lint: over140=9 deep=0 -->", LONG, 1),
    ("an over140= marker is not raised to meet a file that got worse",
     "<!-- pending-lint: over140=1 deep=0 -->", LONG + "\n" + LONG, 1),
    ("no marker seeds at the real count",
     "", LONG + "\n" + LONG, 2),
]

# (label, pending_body, backlog_text_or_None, expect_failure)
PAIRING_TEST_CASES = [
    ("no BACKLOG.md skips pairing", "- **[042]** x\n", None, False),
    ("matched id passes", "- **[042]** x\n", "# B\n\n## 042 - a\n\ndetail\n", False),
    ("a heading with no slug still pairs", "- **[042]** x\n", "# B\n\n## 042\n\ndetail\n", False),
    ("bullet with no id fails", "- plain bullet\n", "# B\n\n## 042 - a\n\ndetail\n", True),
    ("a slug id is not an id", "- **[some-slug]** x\n", "# B\n\n## some-slug\n\nd\n", True),
    ("fewer than three digits fails", "- **[42]** x\n", "# B\n\n## 42 - a\n\nd\n", True),
    ("id with no heading fails", "- **[042]** x\n- **[118]** y\n", "# B\n\n## 042 - a\n\nd\n", True),
    ("heading with no bullet fails", "- **[042]** x\n", "# B\n\n## 042 - a\n\nd\n\n## 118 - b\n\nd\n", True),
    ("duplicate id fails", "- **[042]** x\n- **[042]** y\n", "# B\n\n## 042 - a\n\nd\n", True),
    ("duplicate heading fails", "- **[042]** x\n", "# B\n\n## 042 - a\n\nd\n\n## 042 - a\n\nd\n", True),
    ("the empty-section placeholder needs no id", "- Sin pendientes.\n", "# B\n", False),
    ("a sub-bullet needs no id", "- **[042]** x\n  - detail\n", "# B\n\n## 042 - a\n\nd\n", False),
    ("a Notas bullet needs no id",
     "\n## Notas\n\n- Entrega el 17/09/2026.\n", "# B\n", False),
    ("Notes is the same section under its English name",
     "\n## Notes\n\n- Due 17/09/2026.\n", "# B\n", False),
    ("a `###` inside Notas does not reopen pairing",
     "\n## Notas\n\n### Fechas\n\n- Entrega el 17/09/2026.\n", "# B\n", False),
    ("the exemption ends at the next `##`",
     "\n## Notas\n\n- a note\n\n## Tema\n\n- plain bullet\n", "# B\n", True),
    ("a Notas bullet still obeys the cap",
     "\n## Notas\n\n- " + "x" * 200 + "\n", "# B\n", True),
    ("an entry whose bullet moved to Notas is orphaned",
     "\n## Notas\n\n- **[042]** x\n", "# B\n\n## 042 - a\n\nd\n", True),
]

# (label, pending_body, backlog_text, queue_text_or_None, expect_failure)
QUEUE_TEST_CASES = [
    ("a queue row mirrored by an En curso bullet passes",
     "\n## En curso\n\n- **[042]** doing the thing (some-slug)\n", "# B\n",
     "# Q\n\n## P0\n\n- [ ] thing\n  - **ID**: some-slug\n  - **Origin**: x\n  - **Acceptance**: `true`\n",
     False),
    ("a queue row with no En curso section fails",
     "\n## T\n\n- Sin pendientes.\n", "# B\n",
     "# Q\n\n## P0\n\n- [ ] thing\n  - **ID**: some-slug\n  - **Origin**: x\n  - **Acceptance**: `true`\n",
     True),
    ("an En curso bullet whose id still has a BACKLOG.md heading fails",
     "\n## En curso\n\n- **[042]** doing the thing (some-slug)\n", "# B\n\n## 042 - a\n\nd\n",
     "# Q\n\n## P0\n\n- [ ] thing\n  - **ID**: some-slug\n  - **Origin**: x\n  - **Acceptance**: `true`\n",
     True),
    ("an En curso bullet naming no row slug fails",
     "\n## En curso\n\n- **[042]** doing something unrelated\n", "# B\n",
     "# Q\n\n## P0\n\n- [ ] thing\n  - **ID**: some-slug\n  - **Origin**: x\n  - **Acceptance**: `true`\n",
     True),
    ("an En curso bullet with no **[NNN]** id fails",
     "\n## En curso\n\n- doing the thing (some-slug)\n", "# B\n",
     "# Q\n\n## P0\n\n- [ ] thing\n  - **ID**: some-slug\n  - **Origin**: x\n  - **Acceptance**: `true`\n",
     True),
    ("two En curso bullets naming the same row slug fail",
     "\n## En curso\n\n- **[042]** doing the thing (some-slug)\n"
     "- **[043]** also doing the thing (some-slug)\n", "# B\n",
     "# Q\n\n## P0\n\n- [ ] thing\n  - **ID**: some-slug\n  - **Origin**: x\n  - **Acceptance**: `true`\n",
     True),
    ("an empty queue and no En curso section passes",
     "\n## T\n\n- Sin pendientes.\n", "# B\n", None, False),
    ("an En curso bullet whose id is reused by a theme-section bullet fails",
     "\n## T\n\n- **[042]** other item\n\n## En curso\n\n- **[042]** doing the thing (some-slug)\n",
     "# B\n\n## 042 - a\n\nd\n",
     "# Q\n\n## P0\n\n- [ ] thing\n  - **ID**: some-slug\n  - **Origin**: x\n  - **Acceptance**: `true`\n",
     True),
]


def self_test():
    import tempfile
    bad = []
    for label, text, should_fail in SELF_TEST_CASES:
        if bool(long_blocks(text)) != should_fail:
            bad.append(f"  {label}: expected {'reject' if should_fail else 'accept'}, got the opposite")

    for label, text, should_fail in COMMENT_TEST_CASES:
        if bool(long_blocks(text)) != should_fail:
            bad.append(f"  {label}: expected {'reject' if should_fail else 'accept'}, got the opposite")

    for label, text, expected in DEPTH_TEST_CASES:
        got = max([d for k, _, _, d, _s in blocks(text) if k == "bullet" and d is not None] or [0])
        if got != expected:
            bad.append(f"  {label}: expected max depth {expected}, got {got}")

    def run(pending, backlog=None, queue=None):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "PENDING.md"), "w", encoding="utf-8") as fh:
                fh.write(pending)
            if backlog is not None:
                with open(os.path.join(d, "BACKLOG.md"), "w", encoding="utf-8") as fh:
                    fh.write(backlog)
            if queue is not None:
                with open(os.path.join(d, "QUEUE.md"), "w", encoding="utf-8") as fh:
                    fh.write(queue)
            failures, notices = [], []
            check(d, failures, notices)
            return failures

    for label, marker, body, should_fail in MARKER_TEST_CASES:
        got = bool(run("# P\n\n" + marker + "\n\n## T\n\n" + body))
        if got != should_fail:
            bad.append(f"  {label}: expected {'reject' if should_fail else 'accept'}, got the opposite")

    for label, marker, body, expected in RATCHET_TEST_CASES:
        with tempfile.TemporaryDirectory() as d:
            head = "# P\n\n" + (marker + "\n\n" if marker else "")
            with open(os.path.join(d, "PENDING.md"), "w", encoding="utf-8") as fh:
                fh.write(head + "## T\n\n" + body)
            ratchet(d)
            written = MARKER_RE.search(open(os.path.join(d, "PENDING.md"), encoding="utf-8").read())
        got = None if written is None else written.group("over")
        if got != str(expected):
            bad.append(f"  {label}: expected over140={expected}, got {got}")

    for label, body, backlog, should_fail in PAIRING_TEST_CASES:
        head = "# P\n\n<!-- pending-lint: over140=0 deep=0 -->\n\n## T\n\n"
        got = bool(run(head + body, backlog))
        if got != should_fail:
            bad.append(f"  {label}: expected {'reject' if should_fail else 'accept'}, got the opposite")

    for label, body, backlog, queue, should_fail in QUEUE_TEST_CASES:
        head = "# P\n\n<!-- pending-lint: over140=0 deep=0 -->\n\n"
        got = bool(run(head + body, backlog, queue))
        if got != should_fail:
            bad.append(f"  {label}: expected {'reject' if should_fail else 'accept'}, got the opposite")

    total = (len(SELF_TEST_CASES) + len(COMMENT_TEST_CASES) + len(DEPTH_TEST_CASES)
             + len(MARKER_TEST_CASES) + len(RATCHET_TEST_CASES) + len(PAIRING_TEST_CASES)
             + len(QUEUE_TEST_CASES))
    if bad:
        print("pending-lint self-test FAILED:")
        print("\n".join(bad))
        return 1
    print(f"pending-lint self-test: {total} cases, all as expected.")
    return 0


def main():
    argv = sys.argv[1:]
    if "--self-test" in argv:
        return self_test()

    flags = {a for a in argv if a.startswith("--")}
    roots = [a for a in argv if not a.startswith("--")] or ["."]

    if "--ratchet" in flags:
        return max(ratchet(r) for r in roots)

    failures, notices = [], []
    for r in roots:
        if not os.path.isdir(r):
            failures.append(f"{r} is not a directory")
            continue
        check(r, failures, notices)

    for n in notices:
        print(f"  note: {n}")
    if failures:
        for f in failures:
            print(f"  {f}")
        print(f"\n{len(failures)} PENDING.md problem(s). No block over {PROSE_LIMIT} chars, "
              f"no bullet past level {MAX_DEPTH}, every id paired with BACKLOG.md.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
