# 2026-08-31 - Baseline grid and button scale

## Objective

Put the two columns of the portfolio on one vertical grid, make the two filled buttons visually larger, and delete the 9 orphan PNGs left by the previous session.

Items **204** and **318** of `../hub-career/PENDING.md`. Continues `2026-08-31-markup-and-performance-pass.md`, which is closed; this is its `Next:`.

## The obstacle, found before planning

`scripts/css-lint.py` holds two scales that cannot both be satisfied. Spacing is in pixels — `{0, 4, 8, 12, 16, 24, 32, 48, 64}` — and `line-height` is in ratios — `{1.2, 1.3, 1.4, 1.6}`. No ratio in that set, multiplied by any size in the font-size scale, gives an integer:

| size | ×1.2 | ×1.3 | ×1.4 | ×1.6 |
|---|---|---|---|---|
| 14px (`0.875rem`) | 16,8 | 18,2 | 19,6 | 22,4 |
| 16px (`1rem`) | 19,2 | 20,8 | 22,4 | 25,6 |
| 18px (`1.125rem`) | 21,6 | 23,4 | 25,2 | 28,8 |
| 24px (`1.5rem`) | 28,8 | 31,2 | 33,6 | 38,4 |
| 32px (`2rem`) | 38,4 | 41,6 | 44,8 | 51,2 |

So no text block can land on the grid while the ratio scale stands, and no amount of padding fixes it: a fractional text box moves every element under it off the grid.

The second half is the buttons. Neither `.sidebar-link` nor `.cta` declares `line-height`, so both inherit `normal`, which in Geist is about 1,28. That is where the measured 34px and 44,5px come from, and it is a hole in the lint: the `line-height` check validates a declared value and never asks for one.

## Decision, taken by Pablo at session start

`line-height` stops being a ratio and becomes a pixel value on a 4px grid. Reading rhythm gets slightly airier: body text goes from 25,6px to 28px.

New allowed set, replacing `{1.2, 1.3, 1.4, 1.6}`:

| px | used by |
|---|---|
| `20px` | 14px text: nav, card description, article context, sidebar headline, prev/next |
| `24px` | 16px sidebar name, 18px h3, button labels |
| `28px` | 16px reading text: bio, lead, article paragraphs |
| `32px` | 24px h2 and card titles |
| `40px` | 32px h1 |

## Plan

1. Measure both columns as rendered, in the browser, before touching anything: every block's outer height and top offset, so the "after" has something to compare against.
2. Replace every `line-height` in `styles.css` with its px value from the table above, and declare one on `body` so nothing falls through to `normal`.
3. Give `.sidebar-link` and `.cta` an explicit `line-height` and larger padding, and take both off `display: inline-block`, which puts the button on a line box whose strut adds leading the box height does not account for. Target heights: `.sidebar-link` 44px (from 34px), `.cta` 56px (from 44,5px), keeping the sidebar button the more compact of the two.
4. Swap the `line-height` scale in `scripts/css-lint.py` to the px set, and add the check that was missing: a rule that declares `font-size` must declare `line-height`.
5. Re-measure both columns and confirm every vertical step is a multiple of 4.
6. Delete the 9 orphan PNGs in `media/` — item **318**. `social-thumb.png` stays, it is the Open Graph image and it is referenced twice; `media/favicon/` is untouched.
7. Run `githooks/pre-commit` and commit.

## Risks

- The reading rhythm of the articles changes on every paragraph. The 2026-05-16 audit tuned that deliberately, so this is Pablo's to look at before anything is pushed.
- Step 4 turns a check that passes today into one that may fail on rules the audit never touched. If the fallout is wide, the `font-size`-implies-`line-height` check is the half to drop, not the px scale.
- Nothing is pushed. `main` is 4 commits ahead of `origin/main` and GitHub Pages still serves `03eb102`.

## Execution

## Result
