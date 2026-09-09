# 2026-08-31 - Baseline grid and button scale

## Objective

Put the two columns of the portfolio on one vertical grid, make the two filled buttons visually larger, and delete the 9 orphan PNGs left by the previous session.

Items **204** and **318** of `../my-career/PENDING.md`. Continues `2026-08-31-markup-and-performance-pass.md`, which is closed; this is its `Next:`.

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

1. **Measured first, in the browser.** The extension's tab renders at 461px and `resize_window` does not move it, so the desktop layout was forced with an injected stylesheet that pins `.layout` to 880px and `.content` to 560px — the real desktop widths, so text wraps identically. Every block in both columns came back fractional: `.sidebar-identity` 150,09, `.sidebar-link` 34, `.nav-item` 35,59, `h2` 31,2, `.bio` in multiples of 25,6, `.cta` 44,5.

2. **A third cause the plan did not have.** The sidebar avatar is an `img` with no `display`, so it sits on a line box and the strut adds its descender below the baseline: 64 + 4,49. Every inline image, video and inline-block button in the file does the same. So the fractional offsets had three sources, not two — the ratio line-heights, the undeclared button line-heights, and the line-box strut under every inline media box.

3. **The px scale landed** across 24 rules, plus `line-height: 24px` on `body` so nothing falls through to `normal` again.

4. **`.sidebar-link` is 44px and `.cta` is 56px**, from `line-height` plus vertical padding. Both moved to `display: block; width: fit-content`, which takes them off the line box entirely.

5. **Two rules had been dead since February.** `.content-view p` at specificity (0,1,1) beat `.card-desc` and `.article-context` at (0,1,0), rendering both at 16px `--text-secondary` instead of the declared 14px `--text-muted`. `git log -S` puts `.card-desc` in `5e71908` and `.content-view p` in the later `2cee7b4`, both 2026-02-19, so this is a regression in the redesign and not a decision. Scoped the four affected classes under `.content-view` so the declarations win. The card descriptions and the article context lines are visibly smaller and greyer than before.

6. **`hr` and `.prev-next` each contributed a stray 1px.** `hr` is now `height: 4px` and keeps its 1px `border-top`, which under the global `box-sizing: border-box` occupies exactly 4px. `.prev-next` draws its rule with `box-shadow: inset 0 1px 0 var(--border)` instead of a border, so the box is padding plus content.

7. **`scripts/css-lint.py`** took the px scale, and the value extraction now keeps the unit. It also gained the check that was missing: a rule that sets `font-size` must set `line-height`. Both halves were proved against a fixture with two deliberate violations — the ratio was caught at its line, the undeclared one was reported by selector name.

8. **Item 318**: the 9 PNGs are gone. `media/` went from 8,6 MB to 2,4 MB. The page reloaded with 15 images and 0 broken, all WebP.

9. **After Pablo's review** (`8e942d0`). He approved the grid and the button sizes, and asked for one LinkedIn button instead of two: out of the About view, into `.mobile-header` under the headline, which is the shape the sidebar already had. `.sidebar-link` serves desktop, `.cta` serves mobile, and neither breakpoint shows both.

10. **`.headline` was the fifth rule with the same defect** and the first pass missed it. `.content-view p` had been rendering it at 28px `--text-secondary` against the 24px `--text-muted` it declares, so the mobile header is 8px shorter now and still a multiple of 4. Measured after the change: `.mobile-identity` 248, `.cta` 56, `hr` 4, 32px gaps on both sides of the button, `.mobile-header` 372. Desktop re-measured at 52 block boxes, 0 off grid, and `.cta` does not render there at all.

11. **The gap above the mobile button, in two passes.** Pablo read 32px as too much, and the first correction to 24px was still too much; it sits at 16px, the value `.sidebar-headline` already used, so the two breakpoints space the identity block identically. The gap belonged to the headline's `margin-bottom` and not to the button's `margin-top`, because adjacent margins collapse and the larger one wins: lowering only the button would have changed nothing. Each gap now has one owner — the headline owns the 16px down to the button, `.cta` owns the 32px down to the rule. `.mobile-header` went 372px to 356px and stayed on the grid.

12. **Item 318 broke a script and the session almost shipped it.** `scripts/gen-social-thumb.py` held an absolute `AVATAR` path to `media/2026-avatar.png`, one of the 9 files `1707eff` deleted, so the next run would have failed on its first open. Found only while checking a memory note that still named the PNG, which is to say: the check that caught it was not part of deleting the files. Repointed to the webp in `1a5dc3d`. The grep run before the deletion covered `index.html`, `resume.html` and `styles.css`, and a deletion sweep has to cover `scripts/` too.

## Findings not acted on

- `resume.html` carries its own `<style>` block and still loads Inter and Source Serif from `fonts.googleapis.com`. The previous session removed that origin from `index.html` and this one did not touch `resume.html`, so the site still has a page that reaches Google for fonts.
- A strict baseline grid across the whole page is unreachable and was not attempted. An image with `aspect-ratio: 16 / 9` at fluid width has a fractional height by construction, and so does any box containing one, which is why the card list is exempt. What landed is a 4px lattice of block-box edges, not baseline-to-baseline alignment across type sizes: two blocks at different font sizes have different half-leading, so their box edges share the lattice while their baselines do not.

## Result

Achieved: both halves of **204** and all of **318**. 53 block-level text boxes were re-measured across the sidebar, the About view and an article, and 0 are off the 4px grid, in both the desktop and the mobile layout. `.sidebar-link` 34px → 44px, `.cta` 44,5px → 56px. Two commits, `b41c07c` and `1707eff`, on `main`.

Pablo reviewed the rendered pages at every step and approved them: the grid and the button sizes first, then the single LinkedIn button, then the 16px above it. Item **204** and item **318** both close.

Pushed to `origin/main` on his OK, which is the branch GitHub Pages serves, and the live `styles.css` was confirmed to carry the new scale rather than trusting the push's exit code. Everything in this session is live, including the WebP conversion and the self-hosted Geist from `2026-08-31-markup-and-performance-pass.md`, which had been sitting unpushed.

Next: item **745**, `resume.html` still loading Inter and Source Serif from `fonts.googleapis.com`, the last third-party origin on the site. Its open question first: whether that page should share `styles.css` and the Geist face at all, or stay a separate document with its own serif.

Agent: Claude Code (Opus 5, 1M) | 2026-08-31
