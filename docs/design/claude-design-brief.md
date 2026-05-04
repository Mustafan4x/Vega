# Claude Design refresh guide

The current canonical design lives at `claude-design-output.html` in this folder. It was produced by Claude Design, approved by the user, and is the visual ground truth for the project.

**You usually do NOT need to come back to Claude Design.** Most design changes are made directly in the terminal via Flow A (see `CLAUDE.md` "Visual design source of truth"). Use Claude Design only when you want a fresh visual exploration (a new theme variation, a brand redirection, a fundamentally different layout).

This document describes how to do that refresh cleanly. The flow:

1. Open Claude Design and start a new project.
2. Upload visual references (the `.webp` files at `/home/mustafa/src/vega/design/` are still relevant; you can also upload screenshots of the current `claude-design-output.html` rendered in your browser).
3. Paste the **Brief** section below as your prompt.
4. After Claude Design produces variations, pick one.
5. Ask Claude Design to package it using the **Output format** section below so the new HTML is structured the same way as the current one.
6. Save the new HTML to `/home/mustafa/src/vega/docs/design/claude-design-output.html`, replacing the old version.
7. In Claude Code, say "I updated the Claude Design output, sync the implementation". The PM will run Flow B per `CLAUDE.md`.

---

## Brief (paste this into Claude Design)

> I'm refreshing the visual design for **Vega**, a Black Scholes options pricer for a quant interview portfolio. The implementation is React with Vite, TypeScript, and Tailwind CSS. The audience is technical (quant trading employers); the visual bar is "serious tool with personality, not a generic SaaS dashboard."
>
> The existing design is the **Oxblood** theme: dark surface, oxblood `#C03A3A` primary, sea green `#34D399` accent, IBM Plex Serif italic for display, Newsreader for numbers, Manrope for UI text, JetBrains Mono for code. I want a fresh exploration; you can keep elements you think work or propose something different. Tell me what you're keeping and what you're changing.
>
> **Screens to design (same set as the current version)**:
>
> 1. **Pricing screen**: input form with five inputs (asset price, strike, time to expiry, volatility, risk free rate), a Calculate button, ticker autocomplete, results panel showing call value, put value, and a row of Greeks (delta, gamma, theta, vega, rho).
> 2. **Heat map screen**: two side by side heat maps (call, put) with volatility shock and stock price shock axes. Toggle between value mode (continuous magnitude scale) and P&L mode (red negative, neutral midpoint at zero, green positive, after the user enters call and put purchase prices). Configurable shock ranges and grid resolution.
> 3. **Model comparison panel**: three prices side by side (Black Scholes, binomial, Monte Carlo) for the same inputs.
> 4. **Backtest screen**: strategy selector (long call, long put, covered call, straddle, etc.), date range picker, P&L curve, summary tile with total P&L and max drawdown.
> 5. **Calculation history**: list of past calculations from the database with timestamp and the five inputs. Clicking a row reloads its inputs.
>
> **Constraints**:
>
> * **Accessibility**: WCAG 2.2 AA contrast on every text, focus rings visible on every interactive element, no color only signaling for the heat map.
> * **Responsiveness**: design at 1440 px desktop first; collapse cleanly to 768 px (tablet) and 375 px (mobile).
> * **Tailwind ready**: every value expressible as a Tailwind token. No arbitrary one off values.
> * **No login UI**: ignore auth screens, profile menus, sign in flows. Avatars are decorative only.
> * **Numbers are the hero**: large, confident type sizes for prices and P&L numbers.
> * **Decimal precision**: prices to 4 decimals, percentages to 2, Greeks to 4. Layouts must accommodate long numeric strings.
>
> **Output format**: produce a **single self contained HTML file** with the structure described in the Output format section of my message below. Match the structure exactly so my downstream tooling can parse it.

---

## Output format (paste this as a follow up after picking a variation)

> Please package the chosen variation into a single self contained HTML file that follows this exact structure (the same structure as my current canonical design at `docs/design/claude-design-output.html`). The downstream tool (Claude Code) reads this structure to extract the Tailwind config and the component anatomy automatically.
>
> **1. Hoist every design decision to CSS custom properties at `:root`.**
>
> At the top of the HTML, in a single `<style>` block, declare every color, font size, font weight, line height, letter spacing, spacing value, border radius, shadow, and animation duration as a CSS variable. Use the same naming convention as the current file:
>
> * `--color-primary-50` through `--color-primary-900`, plus `--color-primary-soft`. Same scale for `accent`, `success`, `danger`, `info`, `neutral`.
> * Semantic colors: `--color-background`, `--color-surface`, `--color-surface-2`, `--color-border`, `--color-text-primary`, `--color-text-muted`, `--color-text-subtle`, `--color-text-inverse`.
> * `--font-sans`, `--font-display`, `--font-number`, `--font-mono`.
> * `--text-display-lg`, `--text-display-md`, `--text-heading-lg`, `--text-heading-md`, `--text-body-lg`, `--text-body-md`, `--text-body-sm`, `--text-caption`, `--text-micro` (each as a fixed rem or `clamp()` value with line height bundled).
> * `--space-0` through `--space-16` on a 4 px scale.
> * `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-card`, `--radius-pill`.
> * `--shadow-sm`, `--shadow-md`, `--shadow-card`, `--shadow-card-hover`, `--shadow-focus`.
> * `--duration-fast`, `--duration-base`, `--duration-slow`, `--ease-standard`, `--ease-emphasized`.
> * Layout: `--layout-sidebar-width`, `--layout-topbar-height`, `--layout-page-max`.
>
> No raw hex codes, rem values, px values, or unnamed durations anywhere else in the HTML. Every other style references a variable.
>
> **2. Label every visual region with `data-component`.**
>
> Use the existing component names verbatim: `LayoutShell`, `Sidebar`, `TopBar`, `MetricCard`, `Tabs`, `DataTable`, `InputForm`, `ResultPanel`, `HeatMap`, `PnlHeatMap`, `GreeksPanel`, `TickerAutocomplete`, `ModelSelector`, `BacktestChart`, `HistoryList`. Inside each component, label sub elements with `data-element` (camelCase). If you add a new component, name it in PascalCase and document it in the manifest below.
>
> **3. Embed a JSON design manifest at the bottom.**
>
> A `<script type="application/json" id="design-manifest">` block with this shape (the same shape as the current file):
>
> ```json
> {
>   "name": "<theme name>",
>   "kind": "dark | light",
>   "tokenScope": ":root",
>   "tokens": { "color": {...}, "typography": {...}, "spacing": {...}, "radius": [...], "shadow": [...], "motion": {...}, "layout": {...} },
>   "components": { "<ComponentName>": { "selector": "[data-component='<ComponentName>']", "elements": [...], "variants": [...] } },
>   "screens": [ { "id": "...", "label": "...", "components": [...] } ],
>   "tailwindSketch": { "theme": { "extend": { "colors": {...}, "fontFamily": {...}, "borderRadius": {...}, ... } } }
> }
> ```
>
> Cover every token, every component, every screen.
>
> **4. Add a design language glossary as an HTML comment at the top.**
>
> Plain English to selector or token mapping. Mirror the structure of the current file's glossary.
>
> **5. One sentence comment above each JSX component definition** (or each component CSS section, if components are defined in CSS rather than JSX). So a downstream tool reading the file knows the purpose of each section without parsing it.
>
> **6. Same self contained runtime as the current file.** Inline React via Babel standalone, no external bundle. The HTML must render the live UI when opened in a browser.

---

## After the new HTML lands

In Claude Code, say something like: "I updated the Claude Design output. Sync the implementation."

The PM session will follow Flow B per `CLAUDE.md`: diff the old HTML against the new one, propose a change list, dispatch the UI/UX Designer and Frontend Developer to apply the changes, log the sync to `STATUS.md`.

If you only want to refresh the design but NOT apply it yet (e.g., you're exploring), keep the new HTML in a side branch or a different filename. The active design is whatever is at `docs/design/claude-design-output.html` on `main`.
