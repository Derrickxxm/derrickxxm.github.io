# DESIGN.md — Derrick Xu · "Codefolio Dark"

> Extracted 2026-10-12 from Derrick's existing portfolio (codefolio-dark-portfolio.derrick-xu84.chatgpt.site), written in the
> awesome-design-md / Stitch format so any agent (ops agent, Codex) can build pages that look like it. Values marked
> "measured" come from the live CSS; everything else is a rule derived from the same page.

## 1. Visual Theme & Atmosphere
- Dark, quiet, engineering-notebook feel. Near-black canvas, one electric lime accent, lots of breathing room.
- "Evidence over decoration": numbers, code, flow arrows and labelled metrics carry the page; no stock photos, no gradients behind text, no glassy cards.
- Voice of the visuals matches the brand line: *Real systems. Built with AI.* — confident, plain, technical.

## 2. Color Palette & Roles (measured)
| Token | Hex | Role |
|---|---|---|
| `--bg` | `#0B0E14` | Page background |
| `--panel` | `#121720` | Cards, code blocks, metric tiles |
| `--panel-2` | `#1C2532` | Raised elements, tag backgrounds (`#212937` for tags) |
| `--line` | `#262E3A` | 1px borders, dividers, header bottom line |
| `--text` | `#F1F5FB` | Primary text, headings |
| `--muted` | `#9BA7B9` | Secondary text, section notes |
| `--dim` | `#748299` | Small uppercase labels, captions |
| `--lime` | `#B5FF5B` | The only accent: eyebrows, section indices, highlighted words in H1, primary button, focus |
| `--lime-ink` | `#122000` | Text on lime buttons |
| `--lime-line` | `#607340` | Outline of secondary lime CTA (e.g. "Let's talk") |
| `--violet` | `#BCABFF` | Rare secondary accent for data series (charts only) |
| `--amber` | `#FFD28A` | Warnings / "in progress" status only |
Rules: lime is used sparingly (≤ 1 primary CTA per viewport). Never put lime text on light backgrounds. No other hues.

## 3. Typography Rules (measured)
- **Body**: system UI stack `-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif`, 16px / 1.7.
- **H1**: `clamp(40px, 4.7vw, 65px)`, line-height 1.2, letter-spacing −2px; one key phrase wrapped in a lime `<span>`. Mobile: 43px, −1px.
- **H2**: 32–34px, line-height 1.3, letter-spacing −1px.
- **H3**: 21px (card titles). Section sub-labels as H3 variant: 12px monospace, uppercase, letter-spacing 2px, `--dim`.
- **Mono** (`ui-monospace, monospace`): eyebrows (13px/1.6, letter-spacing 2px, lime), section indices ("01 / PRODUCTS", 12px), tags (12px), code blocks (13–14px), numeric counters.
- Max two families (system sans + system mono). No webfonts required.

## 4. Component Stylings (measured)
- **Header**: sticky, `#0B0E14ED` + `backdrop-filter: blur(18px)`, 1px bottom `--line`, nav height 86px (72px mobile). Right side: outlined lime "Let's talk" (border `--lime-line`, 9px 17px, radius 5px) — hidden on mobile.
- **Buttons**: `.btn` 12px 22px, 1px `--line` border, radius 5px, 14px/600, transparent. `.btn.primary`: lime fill, `--lime-ink` text.
- **Tags/chips**: 12px mono, `#BCC7D6` on `#212937`, 4px 8px, radius 3px; joined by " · " when inline ("Local-first · Paper-first").
- **Cards**: `--panel` background, 1px `--line`, radius 8px, hover: `transform` + border colour transition .2s. Badge top-right for status ("Public toolkit", "Private component").
- **Metric tiles**: big number (count-up on view) + small muted caption + scope note.
- **Code block**: `--panel`, mono 13px, filename header ("engineering.py").
- **Flow lines**: inline arrow chains ("Cold performance → Transfer → Retention → Real use") instead of diagrams.

## 5. Layout Principles (measured)
- Container `.wrap`: `width: min(1180px, calc(100% - 64px))`; mobile `calc(100% - 36px)`.
- Sections: `padding: 78px 0`; header row = index + H2 on the left, note on the right (`align-items: end`).
- Numbered sections "01 … 07" in reading order; single column of sections, grids inside sections (2–3 cards per row on desktop).

## 6. Depth & Elevation
- Flat. Depth comes only from `--panel` vs `--bg` contrast and 1px borders. No drop shadows except a subtle lime glow on live counters (`usage-glow .8s`).

## 7. Do's and Don'ts
- Do: show real numbers with their scope ("measurement scope" notes), real code, real system names.
- Do: keep one idea per section, one primary CTA per screen.
- Don't: stock imagery, emoji decoration, gradient text, more than one accent colour per component, carousels.
- Don't: show anything outside the public boundary (family, trading P&L/capital, unapproved employer details).

## 8. Responsive Behavior (measured)
- Breakpoints: 950px (grids → 1–2 columns), 650px (nav compacts to 72px, CTA hidden, H1 43px).
- `prefers-reduced-motion`: disable count-up and glow animations (`animation: none; transition: none`).

## 9. Agent Prompt Guide
"Build the page with DESIGN.md: dark `#0B0E14` canvas, `#121720` panels with 1px `#262E3A` borders, single lime accent `#B5FF5B` for eyebrows/indices/primary CTA, system sans body 16/1.7, monospace for labels, tags, code and numbers, numbered sections '01 / NAME' with H2 −1px tracking, container min(1180px, 100%−64px), section padding 78px, flat depth, reduced-motion safe."
