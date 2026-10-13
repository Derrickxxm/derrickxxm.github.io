# Brand UI designer — working rules for agents building this site

This repository is Derrick Xu's public brand site (static HTML/CSS on GitHub Pages). Any agent editing it follows these
rules. Visual authority, in order: `DESIGN.md` (this repo) → this file → general taste.

Adapted, with thanks, from MIT-licensed work: Leonxlnx/taste-skill, ibelick/ui-skills (baseline-ui, improve-ui),
anthropics/skills (frontend-design). Only rules were taken; no third-party scripts are used.

## 0. Design read (do this before writing code)
State one line: "Reading this as: developer brand site for AI engineers, Codefolio-Dark language (DESIGN.md), redesign-preserve."
Dials (taste-skill): DESIGN_VARIANCE 6 · MOTION_INTENSITY 3 · VISUAL_DENSITY 4. Do not raise them without the Owner asking.

## 1. Hard constraints
- Plain HTML + one CSS file + at most a few lines of vanilla JS. No frameworks, no build step, no webfonts, no external
  requests, no trackers, no cookie banners. Must work from any path prefix (relative links only) so the custom domain move
  needs no edits.
- Never remove or rename: `privacy.html`, `terms.html`, `callback/instagram.html`, `google92575d77cab759fa.html`.
  Every page footer links Privacy and Terms and shows derrick.xu84@gmail.com.
- Copy comes only from the ops agent's approved site plan (`site-plan.md`). Do not invent facts, numbers, links or quotes;
  keep `{PLACEHOLDER}` tokens visible to engineering as HTML comments + safe fallbacks (e.g. "coming soon").
- Public boundary: no résumé, employers, family, trading P&L/capital, investment advice.

## 2. Anti-slop rules
- No gradients, no purple, no glow as the main affordance, no glassmorphism except the sticky header blur from DESIGN.md.
- One accent (lime) per view; at most one primary CTA per viewport.
- Avoid the LLM defaults: centered hero over a dark mesh, three identical feature cards in a row, emoji icons, stock images.
  Prefer asymmetric section headers (index + H2 left, note right) and real artefacts (code block, flow line, metric tiles).
- Headings: `text-wrap: balance`; paragraphs: `text-wrap: pretty`; numbers: `font-variant-numeric: tabular-nums`.
- Measure: body copy ≤ 68ch; never full-width paragraphs.
- Spacing on a 4px grid; section padding 78px (DESIGN.md); consistent card padding (24px desktop / 20px mobile).
- Fixed z-index scale (header 10, overlays 20). Respect `safe-area-inset` on the sticky header.

## 3. Motion
- Only `transform` and `opacity`; ≤ 200ms for interaction feedback; ease-out entrances; no looping animation.
- Everything off under `prefers-reduced-motion: reduce`.

## 4. Accessibility (must pass)
- Semantic landmarks (`header`, `nav`, `main`, `section` with headings, `footer`); one H1.
- Colour contrast ≥ 4.5:1 for body text (muted `#9BA7B9` on `#0B0E14` passes; never put `#748299` on panels for body copy).
- Visible focus ring (2px lime outline, 2px offset); skip-to-content link; icon-only links have `aria-label`.
- External links: `rel="noopener"`; social links say where they go.

## 5. Metadata
- `<title>`, meta description, canonical (relative-safe), Open Graph + Twitter card (title, description, an OG image
  rendered in the DESIGN.md style), favicon (the lime `</>` mark), `lang="en"`.

## 6. Visual QA loop (required before handing back)
Render at 1440×900 and 390×844 (and 768×1024). For each, check and fix:
alignment to the container edges · hierarchy (one obvious H1, scannable H2s) · whitespace rhythm between sections ·
line length · accent overuse · tap targets ≥ 44px on mobile · no horizontal scroll · header not covering anchors
(`scroll-margin-top`) · dark backgrounds everywhere (no white flashes).
Report: the design read, what you changed in each QA pass, and anything you could not satisfy.
