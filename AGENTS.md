# Portfolio

## Framework
- Fuente canónica de contexto del proyecto: `AGENTS.md`
- Adapter para Claude: `CLAUDE.md`
- Auditoría: 2026-03-18
- Estado: Clean

## Descripción

Single-page vanilla portfolio (HTML + CSS + JS, no build step). Hosted on GitHub Pages, which serves `main`: a push to `origin/main` is a deploy to production at https://roccella.github.io/portfolio/, with no other step and no staging in between. Pages takes about a minute to rebuild, so `curl` the live `styles.css` rather than trusting the push's exit code.

## Estructura

- `index.html` — sidebar layout with identity/nav + content area. About is the default view, articles are content-views with prev/next navigation
- `styles.css` — dark theme, grid layout (sidebar 240px + content 560px), collapses to single column at 900px
- `fonts/` — the self-hosted Geist woff2
- `scripts/css-lint.py` — default-deny check over `styles.css`, wired into `githooks/pre-commit`. Fails on a colour literal outside `:root`, a spacing, type, line-height or radius value off the scales above, a rule that sets `font-size` without `line-height`, and a token that is declared without being used or used without being declared
- `media/` — images and videos referenced by articles

## Este repo no lleva pendientes propios

`portfolio` is a surface, not a source: `../hub-career/` holds the content and decides the work, the way `../arg-work/` does for `../mi-argentina-front/`. So this repo carries no `PENDING.md`, no `BACKLOG.md`, no `HANDOFF.md` and no `QUEUE.md`. Anything pending about these pages is an item in `../hub-career/PENDING.md`, tagged `(portfolio)`.

Its own `PENDING.md` and a rollout `HANDOFF.md` from 2026-08-20 were deleted on 2026-08-31. `scripts/pending-lint.py`, `scripts/queue-lint.py` and `githooks/pre-commit` stay wired and pass with no such file; they are the guard if one ever comes back, not an invitation to write one.

## Fuente de contenido

Articles come from `../hub-career/articles/` drafts. The repo was `blog-articles` until it was renamed on 2026-07-16, and `article-guidelines.md` did not survive the rename; what governed articles is now split in two:

- **`../hub-career/AGENTS.md`** § *Publication format* — opening structure, image types that work, video behavior (autoplay loop muted playsinline), what to avoid
- **Skills `/voice-core` + `/voice-writing`** — voice, register, article structure, titles, concision

`resume.html` and `cover-letter-checkly.md` are not articles and do not follow those two. Pablo is not the writer in the text there, the reader is deciding something, and the register is **`/voice-core` + `/voice-deliverable`**.

### Reader declaration

`skills/voice-core/references/reader.md` § *Name the reader, and write down what they already have* asks for both halves before the first sentence, and gate 4 of `skills/deliverable-gates/` is briefed with this verbatim rather than assuming one.

- **Articles** (`index.html`): a developer or designer who found the piece on its own. They arrive holding nothing about the project it describes, so every term is introduced at first use and this page is where they meet it.
- **`resume.html`, `cover-letter-checkly.md`**: a recruiter or hiring manager at one named company. They arrive holding their own job posting and their own product, and nothing about the projects listed; their vocabulary is the shared one, and each project is introduced by what it did rather than by its name.

When adding or updating an article in the portfolio, follow the two sources above.

## `media/social-thumb.png` lo genera Pablo

`media/social-thumb.png` is the Open Graph and Twitter card image for `index.html` (`index.html:20` and `index.html:27`), 1200x630. Pablo builds it by hand in Figma and exports it. It is the one asset in this repo an agent does not produce.

If it has to change, because the role name in it changed or for any other reason, say so and ask him for a new export. Do not generate, redraw, resize or regenerate it, and do not substitute a rendered HTML page for it.

## The CV never gets committed, under any name

`resume.html` carries Pablo's phone and email, so it and the PDF it prints to are gitignored. On 2026-09-01 an export named `Pablo Roccella - Resume.pdf` landed in the repo, and the plain `resume.pdf` line did not catch it. Pablo decided it stays out, and `.gitignore` now holds `*[Rr]esume*.pdf`.

Nothing carrying that header goes into a commit. This repo publishes to GitHub Pages, so a commit here is a phone number on the open web, and a push cannot be taken back by deleting the file afterwards.

## Design System

All values are defined as CSS variables in `:root` at the top of `styles.css`. Never hardcode colors - always use the tokens.

**Font family:** `var(--font-sans)`, which is `"Geist"` plus a system sans fallback. Body weight `400` (Geist `300` is too thin on dark bg).

Geist is **self-hosted** since 2026-08-31: `fonts/geist-latin-var.woff2`, the latin subset of the variable face, 29.288 bytes, declared in the `@font-face` at the top of `styles.css` and preloaded from `index.html`. `index.html` no longer requests Google Fonts, and the only third-party origin left on that page is Google Analytics. `resume.html` moved onto the same face on 2026-09-01, which closed item 745. It carries its own `<style>` block and shares neither `styles.css` nor the `@font-face`, so it declares Geist a second time against the same file. Every non-ASCII character both pages use sits inside the latin subset, so do not add `latin-ext` without checking first.

**Color tokens:** `--bg` | `--text` | `--text-secondary` | `--text-muted` | `--border` | `--border-hover` | `--accent-1` | `--accent-2` | `--accent-3` | `--accent-sheen` | `--accent-speed` | `--link` | `--on-accent`

**Color usage:** the four `--accent-*` are the button's palette and nothing else uses them as a fill. `--link` for text-as-link (inline links in article paragraphs). Never use an `--accent-*` as text colour: the brightest of the four is 4,17:1 against `--bg` and the other three are under 3:1.

The palette replaced `#4169e1` on 2026-09-03 and was generated in OKLCH by `../gradient-gen/`, which is also where a new one comes from. It is deliberately dark: the four stops carry white text at 9,92:1 | 7,94:1 | 6,46:1 | 4,50:1, and that ceiling on luminance is what makes them unusable as text on `--bg`.

**The decorative left-border on the active nav item is `--accent-sheen`**, the brightest of the four, because it is the only one that clears 3:1 against `--bg` (4,17:1). It is solid and never a gradient: it is 2px wide, and a ramp inside 2px reads as one averaged colour anyway.

**`--link` is `#5791ff`**, `--accent-1`'s hue at the lightness a text colour needs: `oklch(67.1% 0.174 262)`, 6,16:1 against `--bg`. No stop of the palette reaches 4,5:1 on the dark background, so the link cannot be one of them; taking the base fill's hue is what keeps it in the same system. It replaced `#6b8cff`, which was the same lightness and chroma at hue 269,3, tuned to the old accent.

**`resume.html` still carries `#4169e1` hardcoded twice** (the contact links and the download button). That page is on a white background and shares neither `styles.css` nor the tokens, so nothing broke; it is simply the one surface still on the old accent. `--accent-1` gives 9,92:1 there against 4,85:1 today.

`--on-accent` is the text colour **on** the button, and it is pure white for a measured reason. The gate is the brightest stop the text can pass over, `--accent-sheen`: white gives 4,501:1 there and `--text`, an oklch off-white, gives 4,121:1. Do not swap it back to `--text`. The margin over AA is three thousandths, so any new palette has to be measured on that stop before it goes in; `../gradient-gen/` rejects a palette that fails it.

**Focus:** one ring for everything focusable, `2px solid var(--text)` at `2px` offset, always paired with a `:focus { outline: none }`. `--text` is 17:1 against `--bg`; the brightest accent stop is 4,17:1 and is not used for this.

**Type scale:** `0.875rem` (nav, small labels, secondary text) | `1rem` (body) | `1.125rem` (h3 in articles) | `1.5rem` (h2, card titles) | `2rem` (h1)

**Line-height scale:** `20px` (14px text: nav, labels, card and article descriptions) | `24px` (16px sidebar name and button labels, 18px h3) | `28px` (16px reading text) | `32px` (24px h2 and card titles) | `40px` (32px h1)

In pixels on a 4px grid, never a ratio: no ratio times a size in the type scale lands on the spacing scale, so the two could not both hold. Every rule that sets `font-size` must set `line-height`, or it falls through to `normal`, which is a font metric. `css-lint.py` enforces both halves.

**Vertical grid:** every block-level text box and both buttons are a multiple of 4px. Media is exempt: an image sized by `aspect-ratio` at fluid width has a fractional height by construction, and so does any box that contains one. This is a 4px rhythm lattice of box edges, not baseline-to-baseline alignment across type sizes.

**Spacing scale:** 4 | 8 | 12 | 16 | 24 | 32 | 48 | 64px

**Border radius:** `4px` (media/images) | `8px` (cards, buttons) | `9999px` (avatars)

**Button heights:** `.sidebar-link` 44px in the sidebar, on desktop | `.cta` 56px in `.mobile-header`, under the headline, on mobile. One LinkedIn button per breakpoint and never both: the About view had a second one until 2026-08-31. Set by `line-height` plus vertical padding, never by `height`. Both were `display: block` until the glyph went in on 2026-09-03 and are `display: flex; align-items: center; gap: 8px; width: fit-content` now, which keeps both heights to the pixel because the 16px icon is shorter than the 20px and 24px line boxes.

## El botón animado

Both LinkedIn buttons carry four blurred circles orbiting under the text, plus a 16px hand-written SVG glyph at `stroke-width="1.5"`, the first icon in the repo: the prev/next arrows are the entities `&larr;` and `&rarr;`, text and not icons. No icon library enters for one glyph.

The markup is one `.accent-fx` span with four empty spans inside, then the `<svg>`, then `<span class="lb">`. `.accent-fx` is `position: absolute; inset: 0; overflow: hidden; border-radius: inherit`, and the glyph and the label get `position: relative` so they sit above it.

`--accent-1` is the button's `background-color` and shows between the circles; the other three are the circles. **hover and active are a `filter: brightness()`**, not `background-color`: a background colour under an animated fill is invisible.

The blur radius never animates, only a `transform` does, and the four durations are non-integer multiples of `--accent-speed` so the set does not visibly repeat. Each circle walks an eight-step octagon that returns exactly to its first step, so every loop closes.

`prefers-reduced-motion: reduce` sets `animation-iteration-count: 1` alongside the 0,01ms duration. Without that half, an infinite animation at 0,01ms is a flicker rather than a stop.

`../gradient-gen/` is the tool the palette and the mode came from, and it holds the other ten modes that were not chosen.

## Router

The SPA router uses `hashchange` + `window.scrollTo(0, 0)` to switch views.

**Gotcha**: `hashchange` doesn't fire when clicking a link whose hash is already active. Without intervention, the browser processes the `href` as a native anchor and scrolls to the element with that id.

**Fix**: a `click` event listener intercepts all internal `href="#..."` links, calls `preventDefault()`, and either updates the hash (triggering `hashchange`) or calls `scrollTo(0, 0)` directly if the target is already the active view. Never remove or bypass this click handler without replacing this behavior.

## Agregar un artículo

1. Add nav item in sidebar with `data-target` matching the section id
2. Add `content-view` section/article in `<main>` with the article content
3. Update prev/next links in the new article and its neighbors
4. Add the id to the `views` array in the JS router
5. Videos use `autoplay loop muted playsinline` (no controls)
