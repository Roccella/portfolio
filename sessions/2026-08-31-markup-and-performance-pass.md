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

_Pending._

## Result

_Pending._

Next: step 1, convert the media.
