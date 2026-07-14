# Session — Dadatién portfolio entry

**Date:** 2026-07-14
**Project:** portfolio
**Goal:** Publish the 005-dadatien article as a new portfolio entry (source: `../blog-articles/005-dadatien/draft.md`, validated).

## What was done

- Added Dadatién as the newest article (first after About) across all four touch points:
  - Sidebar nav-item, About article-card (hero cover + card-desc), full `<article id="dadatien">`, and the JS `views` array.
  - Reordered prev/next so the sequence is About → Dadatién → Agent Rules → Tudux → Government → Chat Crecer.
- Media copied to `media/`: `dadatien-store-desktop-mobile.png` (hero/cover), `dadatien-ui-system.png`, `dadatien-platform-config.png`, `dadatien-store.webm`, `dadatien-admin.webm`.
- Videos embedded as `<video autoplay loop muted playsinline>` with webm-only source (Pablo's call: only very old Safari lacks webm; no mp4 fallback). The CSS already had `.content-view video`.
- Internal cross-link: "Tudux" in the seller section links to `#tudux`.
- Article HTML mirrors the validated blog draft (lead = opening hook, italic context block, then the sections).

## Notes

- webp/mp4 fallback intentionally omitted (webm-only).
- `social-thumb.png` untouched (hand-made in Geist; do not regenerate via script).
- PENDING "Sync new blog article" item is a standing rule, left in place.

## Result

Committed and pushed to `origin/main` (GitHub Pages prod).

Agent: Claude Code (Opus 4.8 [1m]) | 2026-07-14
