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
- **`~/.claude/editorial-guide.md`** — voice, tone, conciseness

When adding or updating an article in the portfolio, follow those guidelines.

## Adding an Article

1. Add nav item in sidebar with `data-target` matching the section id
2. Add `content-view` section/article in `<main>` with the article content
3. Update prev/next links in the new article and its neighbors
4. Add the id to the `views` array in the JS router
5. Videos use `autoplay loop muted playsinline` (no controls)
