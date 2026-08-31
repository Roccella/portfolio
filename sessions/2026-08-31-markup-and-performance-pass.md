# 2026-08-31 - Markup and performance pass

## Objective

Make `index.html` a page that is worth pointing at as an example of correct markup, and cut what the visitor actually downloads. Triggered by `hub-career` item **519**, which turned out to be misdirected: the session's first output is a rewritten 519.

## Origin: why 519 was wrong

519 asked to extract the embedded `<style>` from `resume.html` into `styles.css` and centralise spacing and typography as variables there.

Two facts kill the first half:

- `resume.html` is in `.gitignore` and is not tracked. `https://roccella.github.io/portfolio/resume.html` returns **404** (verified with `curl` on 2026-08-31). `../hub-career/CONVENTIONS.md:87` records the reason: the page carries Pablo's phone and email, so it is updated locally and never pushed.
- The two pages share no scale to centralise. `index.html` is Geist on a dark theme; `resume.html` is Inter plus Source Serif 4 on a light theme, and its `@media print` block is the whole point of the file.

So moving that CSS into `styles.css` would add light-theme tokens to the stylesheet every visitor downloads, in order to tidy a file that never crosses a network. Inline CSS on a single-purpose local file is the correct architecture here, not a defect.

**Pablo's decision, 2026-08-31**: `resume.html` stays local. Its `<style>` block stays inline, and its markup is out of scope for this session.

The second half of 519 does have a target, and it is in the file 519 never mentions: `styles.css` writes the stack `"Geist", -apple-system, BlinkMacSystemFont, Arial, sans-serif` **13 times** instead of reading a `--font-sans` token.

## Initial state, measured

| Asset | Size |
|---|---|
| `index.html` | 40.438 bytes, 13.960 gzipped |
| `styles.css` | 7.525 bytes |
| `media/` | 8,2 MB total, 10 PNG + 2 WebM |
| `media/agent-rules-cover.png` | 1.630.822 bytes, 1672x941 |
| `media/2026-avatar.png` | 705.895 bytes, 770x770, rendered at 64px |

Seven of the ten PNGs are 1800px or 1920px wide. The content column is 560px, so they are roughly 3,4x oversized even for a 2x display. Markup and CSS together are under 1% of the page weight.

**External origins:** `fonts.googleapis.com` and `fonts.gstatic.com` (`index.html:11-13`), plus `googletagmanager.com` (`index.html:31`).

**Pablo's decision, 2026-08-31**: Google Analytics stays. Self-hosting Geist still removes two of the three origins.

## What the browser actually requests, measured 2026-08-31

Loaded the live site in Chrome and read the network panel, rather than reasoning about it. The default About view makes **6 requests**:

| Request | Transfer |
|---|---|
| `index.html` | 13.960 (gzip) |
| `styles.css` | 7.525 |
| `media/2026-avatar.png` | 705.895 |
| `googletagmanager.com/gtag/js` | 169.778 (brotli, 517.076 raw) |
| `fonts.googleapis.com/css2` | 1.846 |
| `fonts.gstatic.com` Geist woff2 | 29.288 |

Two hypotheses were falsified by this:

- **The 8,2 MB is not first-load cost.** Article images carry `loading="lazy"` and every article lives in a `hidden` `<article>`, so a visitor who reads only About downloads none of them.
- **The two WebM files do not download on the About view.** Chrome does not fetch a `<video autoplay>` whose `<article>` is `hidden`. Re-encoding them at CRF 36 only recovered 24% and 27%, so they stay as they are.

So the first-load picture is one image and one analytics script. `media/2026-avatar.png` is 705.895 bytes at 770x770 to be drawn at 64px, and it is 78% of the bytes on that view. `gtag.js` is the second largest, and it is JavaScript, which costs parse and main-thread time on top of its transfer.

The 8,2 MB still matters, just not on the first paint: it is what anyone who opens an article pays.

## Media conversion, trial run

Converted every PNG to WebP in a scratch directory at `-q 82`, resized to 1200px (the content column is 880 - 240 sidebar - 64 gap = 576px, so 1152px at 2x), the avatar to 256px. Visually checked `agent-rules-chart` at 1:1: the diagram text stays crisp.

| | PNG | WebP | Saved |
|---|---|---|---|
| 9 files | 6.513.375 | 393.896 | **94%** |
| `2026-avatar` alone | 705.895 | 5.414 | 99% |

`social-thumb.png` is excluded: it is the Open Graph image at 22.666 bytes, and scrapers are unreliable with WebP.

## Markup findings, verified

- **No `<h1>` on desktop.** The only `<h1>` is `index.html:66`, inside `.mobile-header`, and `styles.css:152` sets `display: none` on it above 900px. `display: none` removes the element from the accessibility tree, so the desktop outline starts at `<h2>`.
- **`.sidebar-nav` is six bare `<a>` in a flex container** (`index.html:49-56`), with no `<ul>`. A screen reader announces neither a list nor its item count, and offers no way to skip it.
- **`.article-list` cards** have the same shape: anchors with no list semantics.
- **`<video>` elements** carry `autoplay loop muted playsinline` but no `preload` attribute and no fallback content. The two WebM files are 1.017.700 and 955.845 bytes.
- **Images lack `width`/`height` attributes**, so the layout shifts as each one arrives. `loading="lazy"` is already present on all but the two avatars; `decoding` is on none.

## Plan

1. **Media.** Convert the nine content PNGs to WebP at 1200px and the avatar at 256px, repoint `index.html` and the local `resume.html`, verify the rendered pages, then delete the PNGs in a separate commit. Measured: 6.513.375 down to 393.896 bytes. The avatar alone takes the About view from 757.000 to roughly 57.000 bytes.
2. **Self-host Geist.** One latin-subset woff2 of **29.288 bytes**, an `@font-face` in `styles.css` with `font-display: swap`, a `<link rel="preload" as="font" crossorigin>`, and the two `preconnect` plus the render-blocking Google Fonts stylesheet come out of `index.html`.

   Decided 2026-08-31 after measuring both sides. On a first visit the current setup chains two TLS handshakes before the font is even requested: `fonts.googleapis.com` for a render-blocking stylesheet, which is what reveals the `fonts.gstatic.com` URL. Self-hosted, the file comes from an origin already connected and preloads in parallel with `styles.css`.

   The one metric that favours Google is repeat visits: `gstatic.com` sends `cache-control: max-age=31536000` against GitHub Pages' `max-age=600` with an ETag. That difference costs one 304 with no body, on a connection that `index.html` and `styles.css` are revalidating anyway under the same header.

   The shared-cache argument that used to justify Google Fonts no longer applies, because browsers partition the HTTP cache by top-level site. Separately, `fonts.googleapis.com` is blocked in China, where a render-blocking stylesheet stalls the page until the request times out.
3. **`index.html` markup.** Fix the desktop `<h1>`, wrap both navs in `<ul>`, add `width`/`height`/`decoding` to images, add `preload` and fallback content to the videos.
4. **`styles.css` tokens.** Add `--font-sans` and replace the 13 literal stacks. This is what is left of 519.
5. **Rewrite 519** in `../hub-career/PENDING.md` and `BACKLOG.md` to match what is actually true, or delete it if steps 1-4 close it.
6. **`/review-ui`** at the end, scoped to accessibility. Rhythm and hierarchy were already audited in `2026-05-16-typography-and-rhythm-audit.md`.

## Risks

- The PNG-to-WebP conversion is the only step that touches tracked binaries. Originals stay in the tree until the rendered pages are checked, and only then get removed in a separate commit.
- `resume.html` also references `media/2026-avatar.png`. It is gitignored and local, so any rename in `media/` has to be applied there by hand or it breaks silently with no CI to catch it.
- Wrapping the nav in `<ul>` changes the flex layout, since `.sidebar-nav` currently lays out its anchors directly.

## Execution

All five planned steps landed, plus a sixth the review added.

**1. Media** (`a0a61a6`). Nine PNGs converted to WebP with `cwebp -q 82`, content images resized to 1200px and the avatar to 256px. 6.513.375 down to 393.896 bytes. `index.html` and the local `resume.html` repointed; the PNGs stay in the tree until Pablo checks the rendered pages, tracked as item **318** in `../hub-career/PENDING.md`. `social-thumb.png` stays PNG because it is the Open Graph image and scrapers are unreliable with WebP.

**2. Geist self-hosted** (`a0a61a6`). `fonts/geist-latin-var.woff2`, 29.288 bytes, declared with `font-display: swap` and preloaded. The two `preconnect` and the render-blocking Google Fonts stylesheet came out. Verified in Chrome: the woff2 is now the second request, ahead of `styles.css`. All five non-ASCII characters across both pages (`·`, `á`, `é`, `ñ`, `ó`) sit inside the latin subset, so no `latin-ext` is needed.

**3. `index.html` markup** (`a0a61a6`). The sidebar identity became the desktop `<h1>`; the `h1` display rule was scoped to `.mobile-header h1` so `.sidebar-name` keeps its own 1rem size. Both navs and the article grid became `ul`/`li` with `aria-label`, the router now sets `aria-current="page"`, the two empty `<span>` spacers came out and prev/next position themselves by class instead of `:last-child`. Every image got `width`, `height` and `decoding="async"`, and `.content-view > img` got `height: auto` so the new attributes do not squash it. `rel="noopener noreferrer"` on the two `target="_blank"` that lacked it.

**4. `--font-sans`** (`a0a61a6`). Replaces 13 literal copies of the Geist stack. This is what was left of 519.

**5. 519 rewritten** (`hub-career` `04e1dea`). Deleted, and replaced by items **204** (baseline grid plus button scale) and **318** (delete the orphan PNGs).

**6. `/review-ui`**, which the plan scheduled last and which produced two fixes of its own.

## Findings from /review-ui

Measured in the browser, not read off the CSS.

- **Contrast** (`f023043`). `.cta` and `.sidebar-link` painted `var(--text)`, an oklch off-white, on `var(--accent)` #4169e1: **4.438:1**, under AA's 4.5:1. Pure white on the same blue is **4.847:1**, so a new `--on-accent` token fixes it without touching the palette. Note for the record: `2026-05-16-typography-and-rhythm-audit.md` claims "~7.5:1 AAA" for this button. That number was never measured.
- **Target size**. `.prev-next a` was 19,6px tall, under WCAG 2.2 AA's 24x24. `.prev-next` padding-top went 24 to 16 and the link took `padding: 8px 0`, which keeps the border-to-text gap at exactly 24px, puts both values on the spacing scale, and brings the link to 55,2px. Verified: no non-inline focusable is under 24px now.
- **Focus rings**. `.article-card` used `--accent` (3,87:1) while `.cta` and `.sidebar-link` used `--text` (17:1), and `.nav-item`, `.prev-next a` and `.sidebar-identity` had no rule at all. All unified on `--text`, verified by tabbing.
- **Two primary buttons to the same URL** on About. Pablo decided to keep both: the sidebar disappears below 900px, so the body CTA is the only one left on mobile.
- **No style check existed.** No `package.json`, no stylelint, no CI. `scripts/css-lint.py` now runs in `githooks/pre-commit` alongside the two that were there.

## What the browser reports after the changes

Clean: tab order follows visual order, every image has real `alt`, no hand-rolled ARIA, exactly one visible `<h1>` at both desktop and mobile widths with an `H1 H2 H3` outline, and vertical rhythm unchanged from the May audit.

One bug was introduced and caught in the same pass: wrapping the nav anchors in `<li>` un-blockified them, since they had been flex items, and the padding broke the text wrap. `.nav-item { display: block }` restored it.

## Result

Achieved: items 1 through 6 above. The first-load payload of the About view drops from about 757.000 bytes to about 57.000, and the third-party origins go from three to one, the one being the Google Analytics that Pablo chose to keep.

Pending, and it is Pablo's to run: looking at the rendered pages locally before anything is pushed. Nothing in this session left the machine. Once he confirms, item **318** deletes the orphan PNGs.

Next: item 204, the baseline grid pass across the two columns together with the visual size of the buttons.

Agent: Claude Code (Opus 5, 1M) | 2026-08-31
