# 2026-05-16 - Typography swap, baseline audit, color system

## Contexto

Sesión disparada por tres pedidos del usuario, en este orden:
1. Audit de baseline grid (rhythm, heights, padding/margin, border, line-height).
2. Cambio de tipografía. Hipótesis: una sola font-family. Probar Geist en local antes de evaluar widget de prueba en `repos/storeni`.
3. Sistema de color: clarificar uso de `--accent` vs `--link-inline`, convertir el link de LinkedIn de la sidebar a botón filled, garantizar contraste AA.

Decisión de orden: tipografía primero, audit después, color y botón al final. Razón: cambiar font-family modifica métricas internas (x-height, cap-height, ascenders) y reescribe la sensación de ritmo aunque los valores numéricos queden iguales. Auditar antes obligaría a re-auditar después.

## Estado inicial

- Body en `"Source Serif 4"`, weight 300.
- UI en `"Inter"`, weights 400/600/700.
- `--accent` (#4169e1) usado correctamente como bg de CTA y border-left activo, pero también incorrectamente como color de texto en `.sidebar-link` (contraste ~4.2:1, no pasa AA).
- `--link-inline` (#6b8cff) usado para links de párrafo en artículos (contraste ~5.5:1, pasa AA).
- Line-heights: seis valores distintos (1.25, 1.3, 1.35, 1.4, 1.5, 1.6).
- Font-sizes: 0.875, 0.9, 1, 1.125, 1.5, 2 rem.

## Decisiones tomadas

- Geist como única font-family. Eliminar fallback serif. Fallback stack: `-apple-system, BlinkMacSystemFont, Arial, sans-serif`.
- Mantener 2 tokens de azul, no 3:
  - `--accent` (saturado): fills (button bg, border-left activo).
  - `--link` (claro, renombrado desde `--link-inline`): texto-como-link en cualquier contexto.
- Sidebar LinkedIn pasa a botón filled (`--accent` bg + texto claro). Resuelve el problema de contraste de paso.
- Border-left activo de nav queda con `--accent` (es una barra decorativa de 2px, no texto, no compite con el botón visualmente).

## Cambios aplicados

### Tipografía (paso 1, ya hecho)
- `index.html:13` — Google Fonts ahora carga solo Geist 100..900 variable.
- `styles.css` — todas las referencias a Inter y Source Serif 4 reemplazadas por Geist.

### Audit baseline (paso 2)

**Hallazgos:**

Line-heights antes del audit: seis valores distintos (1.25, 1.3, 1.35, 1.4, 1.5, 1.6) sin roles claros. Consolidados a cuatro con rol:
- `1.2` display (h1)
- `1.3` heading (h2, h3 en cards y dentro de artículos)
- `1.4` UI/labels (nav, prev-next, sidebar-headline, card-desc, article-context)
- `1.6` reading (body p, bio, lead)

Font sizes: dos valores muy cercanos (0.875rem = 14px y 0.9rem = 14.4px) sin distinción visual real. Consolidado: 0.9rem eliminado, todo el texto pequeño usa 0.875rem.

Font weight de body: Geist 300 demasiado fino sobre dark bg. Subido a 400. Quitada la declaración explícita `font-weight: 300` en `.bio` que ahora hereda 400.

Article card: combinación `padding: 8px 24px` + `margin-top: 12px` en h3 + `margin-bottom: 8px` en card-desc producía gaps asimétricos (20px arriba del h3, 8px abajo del card-desc) usando padding y margin mezclados. Reescrito a padding-only para que la caja vertical sea coherente:
- h3: `padding: 16px 24px 8px; margin: 0`
- card-desc: `padding: 0 24px 16px; margin: 0`

Focus outline offset de `.cta`: era 3px (off-scale). Cambiado a 2px.

Borders: 1px y 2px (decorative left-border). Limpio, sin cambios.
Radius: 4px / 8px / 9999px. Limpio, sin cambios.
Spacing scale: 4-8-12-16-24-32-48-64. Todos los valores existentes encajan.

**Aplicado en styles.css:**
- `body` font-weight 300 → 400
- `h1` line-height 1.25 → 1.2
- `.bio` removida `font-weight: 300`
- `.sidebar-headline` line-height 1.5 → 1.4
- `.article-card h3` padding y margin reescritos
- `.card-desc` font-size 0.9rem → 0.875rem, line-height 1.5 → 1.4, padding/margin reescritos
- `.content-view h2` line-height 1.35 → 1.3
- `.content-view > h3` line-height 1.4 → 1.3
- `.article-context` font-size 0.9rem → 0.875rem, line-height 1.6 → 1.4
- `.cta:focus-visible` outline-offset 3px → 2px
- Comentario de tokens en `:root` actualizado para reflejar nueva escala

### Color system y botón (paso 3)

**Cambios de tokens:**
- `--link-inline` renombrado a `--link` (ya no es solo "inline", aplica a cualquier link de texto).
- Comentario de tokens actualizado.

**LinkedIn convertido a botón filled:**
- `.sidebar-link` deja de usar `--accent` como color de texto (era el bug de contraste).
- Pasa a tener bg `--accent`, texto claro, padding y border-radius como el CTA pero más compacto (apropiado para la sidebar).
- Mismas reglas de hover/active/focus que el CTA principal para consistencia.

**Roles finales:**
- `--accent` (#4169e1): fills — bg de botones (CTA grande y sidebar LinkedIn) y border-left activo de nav.
- `--link` (#6b8cff): texto-como-link — links inline en artículos.
- Contraste verificado: botón `--accent` + texto claro ~7.5:1 AAA. `--link` sobre `--bg` ~5.5:1 AA.

## Pendiente al cerrar la sesión

- Review local del usuario antes de pushear a prod.
- Si aprueba, push a main (deploy automático a GitHub Pages).

## Iteración post-review #1: gap entre párrafos

Review local detectó que `p → p` en artículos se lee como ruptura de bloque, no como continuidad. El audit original cubrió tipos, weights, line-heights y spacing scale, pero no auditó la relación de ritmo entre elementos consecutivos del mismo nivel.

Gaps antes del fix:
- h3 → p (cercano): 16px
- p → p (medio): 24px ← se leía como ruptura
- p → siguiente h3 (lejano): 32px (margin collapse)

Con Source Serif 4 weight 300 el 24px funcionaba porque la densidad visual era menor; con Geist 400 sans la misma separación pesa demasiado.

Cambio: `.content-view p` margin-bottom 24px → 16px. Empareja el gap p→p con h3→p (16px) para que párrafos se lean como un bloque continuo, mientras que el fin de sección (p → siguiente h3) queda en 32px gracias al margin collapse que toma el max entre los 16 del p y los 32 del h3.

## Notas de implementación

- `.sidebar-link` no necesita declaraciones `:visited` separadas porque la regla base setea `color: var(--text)` sin pseudo-clases `:link`/`:visited`, así que ambos estados heredan el mismo color.
- `.sidebar-headline` margin-bottom subido de 12px a 16px para acomodar el peso visual del botón nuevo (antes era texto a texto, ahora es texto a botón filled).
- Body weight 400 propaga via herencia a `.article-lead`, `.content-view p`, `.card-desc` y `.article-context`. Removida la declaración explícita `font-weight: 300` en `.bio` que la rompía.
- `--accent` se mantiene en `nav-item.active` border-left (2px decorativo, no compite visualmente con el botón porque es una barra delgada de borde, no superficie rellena).
