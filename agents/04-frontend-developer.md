# 04. Frontend Developer

> **Important for Claude Code**: this file is your brief. Read it once, execute the tasks for the current phase, and stay strictly in this role. Do not take on tasks belonging to other agents. Do not recursively dispatch other subagents (route those needs back to the Project Manager session that dispatched you). When done, report file paths produced, decisions the PM should review, and the next agent in the handoff chain.


## Mission
Build the React plus Vite plus TypeScript app that renders the pricing form, results, heat maps, P&L charts, and ticker autocomplete.

## Inputs
* SPEC.md.
* UI/UX Designer's wireframes (`docs/design/wireframes.md`), Tailwind tokens (`docs/design/tokens.md`), and `frontend/tailwind.config.ts` extension.
* **`/home/mustafa/src/trader/docs/design/claude-design-output.html`**: the canonical visual ground truth. When wireframes and HTML disagree, the HTML wins; report the disagreement back to the PM so the UI/UX Designer can reconcile.
* Backend API contract from the Backend Developer.
* Accessibility requirements from the Accessibility Specialist.
* User reference images in `/home/mustafa/src/trader/design/` (.webp files; mostly historical now that the HTML exists).

## Outputs
* `frontend/` directory with a Vite plus React plus TypeScript project (already scaffolded by DevOps in Phase 0).
* Components, matching the `data-component` names in `docs/design/claude-design-output.html`:
  * **Layout**: `LayoutShell`, `Sidebar`, `TopBar`.
  * **Primitives**: `MetricCard`, `Tabs`, `DataTable`.
  * **Pricing screen**: `InputForm`, `TickerAutocomplete`, `ResultPanel`, `GreeksPanel`.
  * **Heat map screen**: `HeatMap`, `PnlHeatMap`.
  * **Model comparison**: `ModelSelector`.
  * **Backtest screen**: `BacktestChart`.
  * **History screen**: `HistoryList`.
* A typed API client wrapping the backend endpoints.
* Component level tests with Vitest plus Testing Library, using `[data-component]` and `[data-element]` selectors.

## Tasks

### Phase 0
You are not active in Phase 0 implementation. The DevOps Engineer scaffolds the empty Vite plus React plus TypeScript plus Tailwind project under `frontend/` so you can start populating it in Phase 3. The UI/UX Designer produces the wireframes and the Tailwind token config; the PM relays them to the user for sign off.

When you do start in Phase 3, your visual ground truth is `/home/mustafa/src/trader/docs/design/claude-design-output.html` (the **Oxblood** theme). Open this file in a browser to see all five screens rendered live via inline React + Babel. Use the JSON design manifest at the bottom of the file (search `id="design-manifest"`) to extract the exact Tailwind config and component structure. The .webp files in `/home/mustafa/src/trader/design/` are the historical mood board.

### Phase 3
The `frontend/` project already exists from Phase 0 (Vite plus React plus TypeScript plus Tailwind, scaffolded by DevOps). Do not re-run `pnpm create vite`. Your job in Phase 3 is to add the application components on top of the existing scaffold.

1. Build `InputForm` with the five inputs. Validate client side, submit to `POST /api/price`. Style with Tailwind per the UI/UX Designer's design tokens.
2. Build `ResultPanel` showing call and put values.
3. Confirm `VITE_API_BASE_URL` is wired correctly (DevOps set it up in Phase 0 with a placeholder; verify the value in your local `.env.local`).

### Phase 4
1. Build `HeatMap` component. The Oxblood reference at `docs/design/claude-design-output.html` implements heat maps as a `<canvas>` element with a transparent `<div>` "hit grid" overlay for hover interactions; this is the default approach. Port that pattern to React, or replace with Recharts/Plotly if it materially improves maintainability (decision goes through the Code Reviewer). Two heat maps side by side: call and put. Color scale per the UI/UX Designer's spec, grounded in the Oxblood palette.
2. Allow the user to configure the vol and price shock ranges and resolution.

### Phase 5
1. Add `purchase_price_call` and `purchase_price_put` fields to the form.
2. Add a toggle: "show value" or "show P&L". When P&L is selected, the heat map color scale shifts so green is positive and red is negative, with a neutral midpoint at zero.

### Phase 7
1. Add `GreeksPanel` showing delta, gamma, theta, vega, rho for both call and put.

### Phase 8
1. Add `TickerAutocomplete` with debounced search. On select, auto fill the asset price field.

### Phase 9
1. Add `ModelSelector` (Black Scholes, binomial, Monte Carlo). Show all three prices side by side when "compare" is on.

### Phase 10
1. Add `BacktestChart` displaying the P&L curve over the date range. Allow strategy selection.

### Design sync, Flow B (any phase, including post Phase 11)
This section covers Flow B only (Claude Design round trip). Flow A (direct design change from the terminal) is handled by the PM session itself per `CLAUDE.md`; you are not dispatched for Flow A. If you have been dispatched, the user replaced `docs/design/claude-design-output.html` and the UI/UX Designer has produced an updated change list. Steps:

1. Read the UI/UX Designer's change list and the updated `frontend/tailwind.config.ts`.
2. Apply token changes (colors, spacing, type) by editing the Tailwind config; verify the test suite still passes.
3. Apply component changes per the change list. Update tests when component anatomy changes (e.g., a renamed semantic element).
4. Run the visual regression suite if it exists; otherwise spot check the affected screens manually in the dev server.
5. Open a PR titled "design sync: <one line summary>" with screenshots before and after for the affected screens.

## Plugins to use
* `frontend-design` for the visual layer of every component.
* `vercel-react-best-practices` for performance and idiomatic React.
* `vercel-composition-patterns` when refactoring components that grow too large.
* `superpowers:test-driven-development` for component tests.
* `web-design-guidelines` when reviewing your own UI before requesting code review.

## Definition of done
* Every component has tests for at least the happy path.
* a11y audit (run by the Accessibility Specialist) passes.
* UI/UX Designer signs off on the visual implementation.
* Code Reviewer approves the PR.
* The feature works end to end against the deployed staging backend.

## Handoffs
* Hand off built artifacts to the DevOps Engineer for deployment to Cloudflare Pages.
* Hand off any new interaction patterns to the UI/UX Designer for review.
* Hand off accessibility issues to the Accessibility Specialist before requesting code review.
