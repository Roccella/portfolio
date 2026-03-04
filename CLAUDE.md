# Portfolio

## About This Project

Single-page vanilla portfolio (HTML + CSS + JS, no build step). Hosted on GitHub Pages.

## Structure

- `index.html` — sidebar layout with identity/nav + content area. About is the default view, articles are content-views with prev/next navigation
- `styles.css` — dark theme, grid layout (sidebar 240px + content 560px), collapses to single column at 900px
- `media/` — images and videos referenced by articles

## Content Source

Articles come from `../blog-articles/` drafts. The editorial voice and formatting rules live there:

- **`../blog-articles/article-guidelines.md`** — structure, media rules, formatting (including video behavior: autoplay loop muted playsinline)
- **Skill `writing-voice`** (`~/.claude/skills/writing-voice/SKILL.md`) — voice, tone, conciseness

When adding or updating an article in the portfolio, follow those guidelines.

## Design System

All values are defined as CSS variables in `:root` at the top of `styles.css`. Never hardcode colors - always use the tokens.

**Fonts:** Plus Jakarta Sans (headings, nav, buttons, UI) | Source Serif 4 (body text, headline, bio)

**Color tokens:** `--bg` | `--text` | `--text-secondary` | `--text-muted` | `--border` | `--border-hover` | `--accent` | `--accent-hover` | `--accent-active` | `--link-inline`

**Type scale:** `0.875rem` (nav, small labels) | `0.9rem` (secondary/context text) | `1rem` (body) | `1.125rem` (h3) | `1.5rem` (h2, card titles) | `2rem` (h1)

**Spacing scale:** 4 | 8 | 12 | 16 | 24 | 32 | 48 | 64px

**Border radius:** `4px` (media/images) | `8px` (cards, buttons) | `9999px` (avatars)

## Router

The SPA router uses `hashchange` + `window.scrollTo(0, 0)` to switch views. Gotcha: `hashchange` doesn't fire when clicking a link whose hash is already active. Without intervention, the browser processes the `href` as a native anchor and scrolls to the element with that id.

Fix: a `click` event listener intercepts all internal `href="#..."` links, calls `preventDefault()`, and either updates the hash (triggering `hashchange`) or calls `scrollTo(0, 0)` directly if the target is already the active view.

Never remove or bypass this click handler without replacing this behavior.

## Adding an Article

1. Add nav item in sidebar with `data-target` matching the section id
2. Add `content-view` section/article in `<main>` with the article content
3. Update prev/next links in the new article and its neighbors
4. Add the id to the `views` array in the JS router
5. Videos use `autoplay loop muted playsinline` (no controls)
