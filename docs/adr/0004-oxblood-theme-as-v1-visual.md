# 0004. Oxblood theme as the v1 visual identity

**Status**: accepted, 2026-05-02.

## Context

A pet project that lives on a resume succeeds or fails partly on first visual impression. A bland grey on white default Tailwind layout reads as unfinished; a distinctive theme reads as intentional. The user (Mustafa) explored the design space externally via Claude Design and committed the output as the canonical visual ground truth at [`../design/claude-design-output.html`](../design/claude-design-output.html).

The chosen theme is named **Oxblood**: a dark surfaced palette built around oxblood `#C03A3A` as primary, sea green `#34D399` as accent, IBM Plex Serif italic for display, Newsreader for numerics, Manrope for UI text, and JetBrains Mono for code. The HTML file exposes every design token as a CSS variable on `:root`, labels every visual region with `data-component` attributes, and ships a JSON design manifest at the bottom that enumerates tokens, components, screens, and a `tailwindSketch` ready to drop into `tailwind.config.ts`.

The implemented React frontend is expected to match this visual personality, not embed the HTML directly.

## Decision

Adopt Oxblood as the v1 visual identity. Treat [`../design/claude-design-output.html`](../design/claude-design-output.html) as the canonical visual ground truth for the project. The UI/UX Designer extracts tokens to [`../design/tokens.md`](../design/tokens.md) and to `frontend/tailwind.config.ts` during Phase 0; the Frontend Developer builds React components against those tokens from Phase 3 onwards. Both flows for design changes (in place edits, or a Claude Design round trip) are documented in [`../../CLAUDE.md`](../../CLAUDE.md) and remain available for the lifetime of the project.

## Consequences

**Positive**:

* A single self contained HTML file is the source of truth for visual decisions, openable in any browser and editable by any agent or by the user directly.
* Tailwind tokens, component anatomy, and screen layout are all derivable from the HTML, so the Frontend Developer never has to guess.
* Design changes can iterate quickly via Flow A (terminal, in place edits) without round tripping through Claude Design every time.

**Negative**:

* The Oxblood HTML must be kept in sync with the implemented React app whenever the design changes; the "Design sync log" in [`../../STATUS.md`](../../STATUS.md) tracks this.
* If the user later wants a fresh visual exploration, that triggers Flow B (a full Claude Design round trip) and is heavier than a single token tweak.
* The theme is opinionated; a future contributor who dislikes oxblood as a primary color will need to either reskin via the CSS variables or run a fresh Claude Design pass.

The tradeoffs are accepted. v1 ships with Oxblood; future versions may revisit.
