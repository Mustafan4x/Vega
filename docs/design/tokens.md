# Vega · Oxblood design tokens

This document is the human readable summary of the design tokens defined in `/home/mustafa/src/vega/docs/design/claude-design-output.html`. The HTML is the visual ground truth; this file restates the tokens for easy reference.

All values come from the `:root` CSS variables (top of the HTML's `<style>` block) and the JSON design manifest at the bottom of the HTML (`<script type="application/json" id="design-manifest">`).

When a token changes, update both the HTML (canonical) and this file (mirror). Token edits flow through `frontend/tailwind.config.ts` once that file exists.

## Theme summary

| Property | Value |
|---|---|
| Theme name | Oxblood |
| Mode | Dark |
| Primary | `#C03A3A` (oxblood) |
| Accent | `#34D399` (sea green) |
| Surface | `#152540` (deep navy) |
| Background | `#0E1A2C` (navy near black) |
| Body text | `#F0EFEA` (parchment) |
| Display family | IBM Plex Serif italic |
| Number family | Newsreader (upright serif, tabular figures) |
| UI family | Manrope |
| Mono family | JetBrains Mono |

## Color palette

### Primary (oxblood)

| Token | Hex | Usage |
|---|---|---|
| `--color-primary-50` | `#FBE9E9` | Lightest tint; rarely used in dark theme. |
| `--color-primary-100` | `#F5C8C8` | |
| `--color-primary-200` | `#E89797` | |
| `--color-primary-300` | `#DA6868` | |
| `--color-primary-400` | `#CD4F4F` | |
| `--color-primary-500` | `#C03A3A` | The oxblood. Primary buttons, brand mark, call value, active nav, axis labels. |
| `--color-primary-600` | `#A23030` | |
| `--color-primary-700` | `#842525` | |
| `--color-primary-800` | `#621A1A` | |
| `--color-primary-900` | `#3F0F0F` | |
| `--color-primary-soft` | `rgba(192, 58, 58, 0.14)` | Active nav background, focus ring. |

### Accent (sea green)

| Token | Hex | Usage |
|---|---|---|
| `--color-accent-50` | `#E5FBF3` | |
| `--color-accent-100` | `#C0F4E0` | |
| `--color-accent-200` | `#8BE7C5` | |
| `--color-accent-300` | `#5EDDAE` | |
| `--color-accent-400` | `#45D9A2` | |
| `--color-accent-500` | `#34D399` | The accent. Put value, status dot, Monte Carlo column accent, success P&L. |
| `--color-accent-600` | `#25B07F` | |
| `--color-accent-700` | `#1B8A63` | |
| `--color-accent-800` | `#126048` | |
| `--color-accent-900` | `#0A3B2C` | |

### Status colors

| Token | Hex | Usage |
|---|---|---|
| `--color-success-500` | `#34D399` | Aliased to accent 500. Positive P&L, ITM tag, status dot. |
| `--color-success-700` | `#1B8A63` | |
| `--color-success-soft` | `rgba(52, 211, 153, 0.14)` | ITM tag background. |
| `--color-danger-500` | `#C03A3A` | Aliased to primary 500. Negative P&L, OTM tag, drawdown. |
| `--color-danger-700` | `#842525` | |
| `--color-danger-soft` | `rgba(192, 58, 58, 0.15)` | OTM tag background. |
| `--color-info-500` | `#7DD3FC` | Binomial column accent. |
| `--color-info-700` | `#0284C7` | |
| `--color-greek-amber` | `#C7A248` | Greek tile accent (Theta). |
| `--color-greek-violet` | `#A78BFA` | Greek tile accent (Rho). |

### Neutrals (the navy palette)

| Token | Hex | Usage |
|---|---|---|
| `--color-neutral-50` | `#F0EFEA` | Document parchment; aliased to text primary. |
| `--color-neutral-100` | `#D7DAE2` | Aliased to text muted. |
| `--color-neutral-200` | `#A9AEC0` | |
| `--color-neutral-300` | `#727891` | Aliased to text subtle. |
| `--color-neutral-400` | `#4D5470` | |
| `--color-neutral-500` | `#2A416A` | Aliased to border. |
| `--color-neutral-600` | `#1C3052` | Aliased to surface 2 (elevated). |
| `--color-neutral-700` | `#152540` | Aliased to surface (cards). |
| `--color-neutral-800` | `#0E1A2C` | Aliased to background (page). |
| `--color-neutral-900` | `#061020` | |

### Semantic surface aliases

| Token | Resolves to |
|---|---|
| `--color-background` | `--color-neutral-800` (`#0E1A2C`) |
| `--color-surface` | `--color-neutral-700` (`#152540`) |
| `--color-surface-2` | `--color-neutral-600` (`#1C3052`) |
| `--color-border` | `--color-neutral-500` (`#2A416A`) |
| `--color-text-primary` | `--color-neutral-50` (`#F0EFEA`) |
| `--color-text-muted` | `--color-neutral-100` (`#D7DAE2`) |
| `--color-text-subtle` | `--color-neutral-300` (`#727891`) |
| `--color-text-inverse` | `#FFFFFF` |

### Document texture

| Token | Value | Usage |
|---|---|---|
| `--paper-rule` | `rgba(240, 239, 234, 0.04)` | Horizontal ruled paper background grid. |
| `--paper-rule-step` | `32px` | Distance between rules. |

## Typography

### Font families

| Token | Stack | Role |
|---|---|---|
| `--font-sans` | `Manrope, Inter, ui-sans-serif, system-ui, sans-serif` | UI labels, inputs, body text. |
| `--font-display` | `IBM Plex Serif, Georgia, serif` (italic) | Card titles, nav items, breadcrumbs, tags, sentence words. |
| `--font-number` | `Newsreader, Iowan Old Style, Georgia, serif` (upright, tabular figures) | Every number on the page. |
| `--font-mono` | `JetBrains Mono, ui-monospace, SF Mono, Menlo, monospace` | Ticker symbols, footers, axis ticks in heat map. |

The display family is applied with `font-style: italic`. Numbers always use Newsreader with `font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1, "lnum" 1`.

### Type scale (size / line height)

| Token | Value | Usage |
|---|---|---|
| `--text-display-lg` | `56px / 1.05` | Hero call/put values. |
| `--text-display-md` | `32px / 1.05` | Backtest summary big stats. |
| `--text-heading-lg` | `24px / 1.2` | Card titles. |
| `--text-heading-md` | `19px / 1.25` | Brand mark, model column names. |
| `--text-body-lg` | `17px / 1.5` | Nav items, breadcrumb. |
| `--text-body-md` | `15px / 1.5` | Body copy, mode tabs. |
| `--text-body-sm` | `14px / 1.5` | Meta lines, suffixes. |
| `--text-caption` | `13px / 1.4` | Tags, pills. |
| `--text-micro` | `11px / 1.3` | Heat map axis ticks, status footer. |

### Weight and tracking

| Token | Value |
|---|---|
| `--weight-regular` | 400 |
| `--weight-medium` | 500 |
| `--weight-semibold` | 600 |
| `--weight-bold` | 700 |
| `--tracking-tight` | -0.01em |
| `--tracking-normal` | 0 |
| `--tracking-wide` | 0.04em |
| `--tracking-caps` | 0.06em |

## Spacing (4 px scale)

| Token | Value | Common use |
|---|---|---|
| `--space-0` | 0 | |
| `--space-1` | 4px | Tight gap, status dot offsets. |
| `--space-2` | 8px | Small gap, sub element separators. |
| `--space-3` | 12px | Sidebar padding, suffix offset. |
| `--space-4` | 16px | Greeks tile padding, control gaps. |
| `--space-5` | 20px | Card padding, section gap. |
| `--space-6` | 24px | Page padding, top bar padding. |
| `--space-7` | 32px | |
| `--space-8` | 40px | |
| `--space-10` | 56px | |
| `--space-12` | 72px | |
| `--space-16` | 96px | |

## Radii

| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | `3px` | Brand mark, ticker autocomplete row. |
| `--radius-md` | `6px` | Inputs, tabs, buttons, icon buttons. |
| `--radius-lg` | `10px` | Greek tiles, model columns. |
| `--radius-card` | `6px` | Cards (alias of radius md, kept separate so cards can drift independently). |
| `--radius-pill` | `999px` | ITM/OTM tags. |

## Shadows

| Token | Value | Usage |
|---|---|---|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.25)` | Active tab elevation. |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.30)` | Ticker autocomplete popover. |
| `--shadow-card` | `0 1px 2px rgba(0,0,0,0.25), 0 6px 16px rgba(0,0,0,0.28)` | Default card shadow. |
| `--shadow-card-hover` | `0 1px 2px rgba(0,0,0,0.25), 0 12px 28px rgba(0,0,0,0.40)` | Card hover. |
| `--shadow-focus` | `0 0 0 3px var(--color-primary-soft)` | Input and button focus ring. |

## Motion

| Token | Value | Usage |
|---|---|---|
| `--duration-fast` | `100ms` | Button press scale, table row hover. |
| `--duration-base` | `180ms` | Default transition (color, background, border). |
| `--duration-slow` | `320ms` | Screen fade. |
| `--ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | Default easing. |
| `--ease-emphasized` | `cubic-bezier(0.22, 0.8, 0.36, 1)` | Screen fade in. |

Reduced motion: respect `prefers-reduced-motion` in the React implementation by short circuiting the screen fade and disabling hover lifts.

## Layout

| Token | Value |
|---|---|
| `--layout-sidebar-width` | `232px` |
| `--layout-topbar-height` | `56px` |
| `--layout-page-max` | `1400px` |

## Z stack

| Token | Value |
|---|---|
| `--z-popover` | `20` |
| `--z-modal` | `40` |

## Glossary cross reference

Plain English phrases map to these tokens (full glossary lives at the top of the HTML):

* "the primary color" / "the oxblood" → `--color-primary-500`.
* "the accent color" / "the green" → `--color-accent-500`.
* "card padding" → `--space-5` applied via `.tr-card`.
* "card radius" → `--radius-card`.
* "the body font" → `--font-sans` (Manrope).
* "the display font" → `--font-display` (IBM Plex Serif italic).
* "the number font" → `--font-number` (Newsreader).
* "the mono font" → `--font-mono` (JetBrains Mono).

## How tokens flow into Tailwind

A drop in Tailwind extension lives at `/home/mustafa/src/vega/docs/design/tailwind-extension.snippet.ts`. The DevOps Engineer inserts that snippet under `theme.extend` in `frontend/tailwind.config.ts` during the Phase 0 frontend scaffold. The extension references the CSS variables above so Tailwind utilities and raw CSS stay in sync; reskinning the app is a single `:root` edit.
