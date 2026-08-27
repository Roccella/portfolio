# Portfolio

## Framework
- Fuente canónica de contexto del proyecto: `AGENTS.md`
- Adapter para Claude: `CLAUDE.md`
- Auditoría: 2026-03-18
- Estado: Clean

## Descripción

Single-page vanilla portfolio (HTML + CSS + JS, no build step). Hosted on GitHub Pages.

## Estructura

- `index.html` — sidebar layout with identity/nav + content area. About is the default view, articles are content-views with prev/next navigation
- `styles.css` — dark theme, grid layout (sidebar 240px + content 560px), collapses to single column at 900px
- `media/` — images and videos referenced by articles

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

## Design System

All values are defined as CSS variables in `:root` at the top of `styles.css`. Never hardcode colors - always use the tokens.

**Font family:** `"Geist"` everywhere, system sans fallback. Body weight `400` (Geist `300` is too thin on dark bg).

**Color tokens:** `--bg` | `--text` | `--text-secondary` | `--text-muted` | `--border` | `--border-hover` | `--accent` | `--accent-hover` | `--accent-active` | `--link`

**Color usage:** `--accent` for fills (button bg, decorative left-border on active nav). `--link` for text-as-link (inline links in article paragraphs). Never use `--accent` as text color, fails AA contrast on dark bg.

**Type scale:** `0.875rem` (nav, small labels, secondary text) | `1rem` (body) | `1.125rem` (h3 in articles) | `1.5rem` (h2, card titles) | `2rem` (h1)

**Line-height scale:** `1.2` (display, h1) | `1.3` (heading, h2/h3) | `1.4` (UI text, labels) | `1.6` (reading, paragraphs)

**Spacing scale:** 4 | 8 | 12 | 16 | 24 | 32 | 48 | 64px

**Border radius:** `4px` (media/images) | `8px` (cards, buttons) | `9999px` (avatars)

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
