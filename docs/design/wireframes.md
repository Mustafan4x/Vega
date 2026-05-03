# Trader · Oxblood wireframes

This document describes the layout and interaction model for each of the five screens in the Trader app. The canonical visual ground truth is `/home/mustafa/src/trader/docs/design/claude-design-output.html`. This file is a written description of what already exists there, anchored to the `data-component` and `data-element` selectors used in the HTML.

When the Frontend Developer scaffolds React components in Phase 3, they should match these `data-component` names and `data-element` parts so the canonical HTML remains useful as a reference.

## Global app shell

The shell is the same on every screen.

* Top level component: `[data-component="LayoutShell"]`.
* Two column CSS grid: `var(--layout-sidebar-width)` (232 px) on the left, `1fr` on the right.
* Document background uses a subtle horizontal ruled paper texture (`--paper-rule` at 32 px steps).

### Sidebar `[data-component="Sidebar"]`

* Width 232 px on desktop, collapses to 64 px (icons only) below 768 px.
* Background `rgba(14, 26, 44, 0.92)` with a thin oxblood soft border on the right.
* Vertical stack: `[data-element="brand"]` (logo plus "Trader" wordmark in IBM Plex Serif italic bold), `[data-element="nav"]` (five nav buttons), `[data-element="footer"]` (status dot plus live timestamp in JetBrains Mono).
* Each `[data-element="navItem"]` is a button with an icon and a label in IBM Plex Serif italic. Active item: `data-active="true"` swaps background to `--color-primary-soft` and text color to `--color-primary-500`, weight bumps to bold.
* The five nav items: Pricing (calculator icon), Heat Map (grid icon), Model Comparison (git compare icon), Backtest (activity icon), History (clock icon).

### Top bar `[data-component="TopBar"]`

* Height 56 px, full width minus sidebar.
* Background `rgba(14, 26, 44, 0.85)` with `backdrop-filter: blur(8px)`; bottom border in `--color-border`.
* Left: breadcrumbs `[data-element="crumbs"]` of the form `Trader / <screen label>`, where `Trader` is `[data-element="crumbMuted"]` and the active screen is `[data-element="crumb"]`.
* Right: `[data-element="actions"]` containing two icon buttons (Theme, Settings) and a circular avatar `[data-element="avatar"]` showing initials.

### Page content slot

* `.tr-page` wraps each screen's content; `padding: 24px`, `max-width: 1400px`, centered.
* Wrapped in a `.tr-screen-fade` div keyed on the active screen; on every screen change it replays the 320 ms fade-in animation (`tr-screen-in` keyframes; opacity 0 to 1 plus 6 px slide-up).

### Breakpoints

The HTML defines three breakpoints; React components must respect all three:

| Breakpoint | Trigger | Effect |
|---|---|---|
| `max-width: 1100px` | Tablet landscape and below | `tr-pricing` collapses to one column; `BacktestChart` summary moves under the chart; heat map grids stack vertically. |
| `max-width: 768px` | Tablet portrait | Sidebar collapses to 64 px icons only, brand name and nav labels hidden; `ResultPanel` becomes one column; `ModelSelector` grid becomes one column; page padding drops to 16 px. |
| `max-width: 480px` | Phone | Greeks panel grid drops from five columns to two. |

## Screen 1: Pricing

URL state: `active === 'pricing'`.

### Layout grid

* Outer wrapper: `.tr-pricing`, two column grid: `380px 1fr`, gap 20 px, items aligned to start.
* Below 1100 px: collapses to one column (input form on top, result panel below).

### Visible components

#### Left column: `[data-component="InputForm"]`

A `.tr-card` with a title row (`Inputs` + `Black–Scholes` meta) and a `[data-element="grid"]` of vertical fields with 14 px gap.

Fields, in order:

1. Ticker. `[data-component="TickerAutocomplete"]` containing `.tr-input` plus a search icon. Typing opens `[data-element="popover"]` with up to six matches; each `[data-element="row"]` shows symbol (mono, oxblood), name (italic serif, muted), and price (Newsreader, primary). Empty state `[data-element="empty"]` renders italic muted text.
2. Asset Price (S), suffix `USD`.
3. Strike (K), suffix `USD`.
4. Time to Expiry (T), suffix `yrs`.
5. Risk Free Rate (r), suffix `%`.
6. Volatility (sigma), suffix `%`.
7. Calculate button (`.tr-btn--primary`, full width, calculator icon).

All numeric fields are `NumField` instances rendered with the `tr-mono` class so values appear in Newsreader with tabular figures. Inputs have a 44 px height, dark inset background `rgba(0, 0, 0, 0.32)`, focus ring uses `--shadow-focus`.

#### Right column: `[data-component="ResultPanel"]`

CSS grid `1fr 1fr` with 20 px gap, three children:

1. Call card. `.tr-card[data-component="MetricCard"][data-variant="call"]`. Head shows title `Call Value` and an ITM/OTM tag (`.tr-tag--success` if intrinsic > 0). Hero number uses `.t-num-hero` (Newsreader 56/1.05 bold) tinted with `--color-primary-500`. Sub line shows `Intrinsic $X · Time $Y` in italic serif muted with primary numbers.
2. Put card. Same anatomy with `data-variant="put"`; hero tinted `--color-accent-500`.
3. Greeks panel. `.tr-card[data-component="GreeksPanel"]` spans both columns (`grid-column: 1 / -1`). Card head: `Greeks` title, `Per share` meta. Body `[data-element="row"]` is a five column grid of `[data-element="tile"]` items (Delta, Gamma, Theta, Vega, Rho). Each tile has: a glyph (Greek letter, italic serif), a value (Newsreader 22 px), a name (italic serif body sm). Tiles carry a 3 px left accent border that cycles through primary, accent, amber, info, violet. Greeks panel only renders once Phase 7 lands; until then the grid row is empty space.

### Interactions

* Typing in any number field updates inputs state; on blur the value is parsed and clamped (NaN to 0). Calculation is reactive (memoized); the explicit Calculate button records a row to history and is the only way to mutate persistence.
* Ticker autocomplete: typing filters; clicking a row sets the asset price S to the ticker's price and closes the popover.
* All inputs have a primary outlined focus ring; hover bumps the border to `rgba(192, 58, 58, 0.35)`.

## Screen 2: Heat Map

URL state: `active === 'heatmap'`.

### Layout grid

* Outer wrapper: `.tr-heatmap`, single column with 20 px gap.
* Two stacked sections: a controls card on top, a `.tr-heatmap-grids` row of two heat maps below (`1fr 1fr` on desktop, stacked below 1100 px).

### Visible components

#### Controls card

`.tr-card.tr-heatmap-controls`. Vertical stack with 16 px gap.

* Mode tabs `[data-component="Tabs"]` with two children `[data-element="tab"]`: `Value` (grid icon) and `P&L` (trending up icon). Active tab: `data-active="true"` switches background to surface and text to primary.
* `.tr-control-grid`: auto fit grid, columns at `minmax(200px, 1fr)`, 14 px gap. Children:
  * Vol shock range pair (two `<input type="range">` for min and max), 5 to 100 percent.
  * Price shock range pair, 50 to 150 percent.
  * Resolution select: 5x5, 9x9, 13x13.
  * In `pl` mode only: two extra NumFields for Call paid and Put paid, both `USD`.

#### Heat map cards

Two side by side cards: `[data-component="HeatMap"]` (Call) and `[data-component="PnlHeatMap"]` (Put). Both share anatomy:

* Card head: title (`Call` or `Put`), meta (`N cells` in value mode, `basis $X` in P&L mode).
* `[data-element="frame"]`: two column grid `36px 1fr`, 4 px gap. Left column is `[data-element="axis"]` (vertical sigma ticks, top axis label `[data-element="axisLabel"]` reading "sigma"). Right column is `[data-element="canvasWrap"]`, a 1:1 aspect square (min 280 px) with a 1 px border and 6 px radius.
* Inside the canvas wrap: a single `<canvas>` rendered via `<canvas data-element="canvas">` painting the bilinear interpolated grid (240x240 image data), and an absolutely positioned `[data-element="hitGrid"]` of `[data-element="cell"]` divs in a CSS grid matching the resolution. Each cell has `cursor: crosshair`; hover shows a 1.5 px white inset ring.
* `[data-element="axisX"]`: a horizontal grid below the canvas with the spot percent ticks, plus an `[data-element="axisLabel"]` reading "spot %".

### Interactions

* Mode tab switches between value and P&L. P&L mode reveals two extra inputs in the controls grid.
* Range sliders update vol and price shock ranges; resolution select changes axis count.
* Hovering a cell shows the title attribute (sigma, spot, dollar value) and the inset ring. The cell's `aria-label` carries the same information for screen readers.
* The canvas redraws inside `useEffect` whenever `grid`, `mode`, `basis`, `min`, `max`, `cols`, or `rows` change.

## Heat map color scale spec

This is the unambiguous color rule for both modes. The Frontend Developer must implement the React heat map with these exact RGB triples and the same midpoint rule as the canonical HTML.

### Value mode (5 stop, min to max)

The canvas paints each cell with a 5 stop ramp interpolated linearly from min to max value across the grid. The midpoint rule is **dynamic**: `t = (v - min) / (max - min)` where `min` and `max` are the actual minimum and maximum values across the rendered grid. There is no fixed midpoint; the ramp covers the full data range.

| Stop | Position (`t`) | RGB | Hex | Role |
|---|---|---|---|---|
| 1 | 0.00 | `(16, 185, 129)` | `#10B981` | Lowest value (cool green) |
| 2 | 0.25 | `(132, 204, 22)` | `#84CC16` | Lime |
| 3 | 0.50 | `(234, 179, 8)` | `#EAB308` | Amber midpoint |
| 4 | 0.75 | `(249, 115, 22)` | `#F97316` | Orange |
| 5 | 1.00 | `(239, 68, 68)` | `#EF4444` | Highest value (hot red) |

Interpolation is segmented linear: pick the segment `seg = floor(t * 4)` (clamped to 3), then linearly blend stop `seg` toward stop `seg + 1` by the fractional remainder. Out of bounds values are clamped.

### P&L mode (diverging, zero anchored)

The midpoint rule for P&L is **fixed at zero** (the breakeven point). Each cell's P&L is `pl = v - basis` where `basis` is the user supplied purchase price. The scale is normalized so a cell's color depth grows symmetrically as P&L moves away from zero:

```
denom = max(0.5, abs(basis) * 0.4) * 3
tn = clamp(pl / denom, -1, 1)
if tn <= 0: stops = stopsNeg, t = tn + 1   // 0..1 across stopsNeg
else:        stops = stopsPos, t = tn       // 0..1 across stopsPos
```

`denom` is a soft normalizer so both small basis cases (where 0.5 dollars dominates) and large basis cases scale gracefully.

#### Negative ramp (`stopsNeg`, 4 stops, P&L from -infinity through zero)

| Stop | Position (`t`) | RGB | Hex | Role |
|---|---|---|---|---|
| 1 | 0.00 | `(185, 28, 28)` | `#B91C1C` | Deepest loss (dark red) |
| 2 | 0.33 | `(239, 68, 68)` | `#EF4444` | Loss |
| 3 | 0.67 | `(252, 165, 165)` | `#FCA5A5` | Mild loss |
| 4 | 1.00 | `(229, 231, 235)` | `#E5E7EB` | Zero (neutral gray) |

#### Positive ramp (`stopsPos`, 4 stops, zero through +infinity)

| Stop | Position (`t`) | RGB | Hex | Role |
|---|---|---|---|---|
| 1 | 0.00 | `(229, 231, 235)` | `#E5E7EB` | Zero (neutral gray) |
| 2 | 0.33 | `(134, 239, 172)` | `#86EFAC` | Mild gain |
| 3 | 0.67 | `(34, 197, 94)` | `#22C55E` | Gain |
| 4 | 1.00 | `(21, 128, 61)` | `#157A3D` | Deepest gain (dark green) |

### Notes for the Frontend Developer

* These color stops are the canonical values used inside the canvas painter in `claude-design-output.html` (function `HeatMap`, constants `stopsValue`, `stopsNeg`, `stopsPos`). They do not match the Tailwind primary or accent palette on purpose: the heat map uses a perceptually balanced diverging scale rather than the brand palette, which would muddy the gradient and confuse value vs P&L states.
* When porting to React, keep the bilinear interpolation in pixel space (240x240 image data) so a 5x5 grid still produces a smooth fill rather than visible cells; the overlaid hit grid handles cell hover.
* Provide a separate hex constant in the React module so it can be unit tested. Suggested location: `frontend/src/lib/heatMapColors.ts`.
* The legend element is not yet implemented; if added, it should sit at `[data-component="HeatMap"] [data-element="legend"]` per the glossary.

## Screen 3: Model Comparison

URL state: `active === 'compare'`.

### Layout grid

* Single `.tr-card[data-component="ModelSelector"]` filling the page.
* Card head: title `Model Comparison`, meta `sigma X% · T Yy` summarizing inputs.
* `[data-element="grid"]`: three column grid (`repeat(3, 1fr)`, 14 px gap). Below 768 px collapses to one column.

### Visible components

Three `[data-element="column"]` cards in this order:

1. Black Scholes (`data-accent="primary"`, oxblood top border).
2. Binomial (`data-accent="info"`, sky blue top border).
3. Monte Carlo (`data-accent="accent"`, sea green top border).

Each column contains:

* `[data-element="modelName"]`: italic serif bold body lg.
* `[data-element="modelTag"]`: italic serif medium caption (e.g., `closed form`, `200 steps`, `50 000 paths`).
* Two `[data-element="modelRow"]` rows separated by a top border: Call and Put labels with `.t-num-display` numbers.

Footer `[data-element="footer"]`: italic serif body sm muted, with `max spread` and `runtime` stats in Newsreader.

### Interactions

* No interactive selection in v1; the card is read only and reflects the inputs from the Pricing screen state. The model selector may grow into a checkbox UI in later phases (Phase 9 wires real pricers behind these columns).

## Screen 4: Backtest

URL state: `active === 'backtest'`.

### Layout grid

* Outer wrapper: `[data-component="BacktestChart"]`, two column grid (`320px 1fr`, 20 px gap). Below 1100 px collapses to one column.
* Three logical regions: controls (left, full height), summary (right top), chart (right below summary).

### Visible components

#### Controls `[data-element="controls"]`

A `.tr-card` aligned to grid start. Vertical stack with 14 px gap:

* Strategy select with the seven strategies: Long Call, Long Put, Covered Call, Cash Secured Put, Long Straddle, Iron Condor, Bull Call Spread.
* From date input (`type="date"`, mono numerals).
* To date input.
* Run backtest button (`.tr-btn--primary`, play icon).

#### Summary `[data-element="summary"]`

Three column grid of stat cards (Total P&L, Max Drawdown, Sharpe). Each card has a `[data-element="stat"]` block with:

* Tiny `tr-label` heading.
* `.t-num-display` value, tinted `.tr-pos` or `.tr-neg` for signed values.
* `.tr-card-meta` sub line.

Below 1100 px the summary moves under the chart and stays in a 3 column grid; below 768 px it stacks to 1 column.

#### Chart `[data-element="chart"]`

A `.tr-card` containing:

* Card head: title `<strategy> · cumulative P&L`, sub line `USD per contract · <from> -> <to>`, meta `<N> trading days`.
* `<svg data-element="curve">` 720x240 viewBox with:
  * Five horizontal grid lines at nice y ticks; the zero line is rendered solid at 25 percent opacity, others dashed at 8 percent.
  * Five x ticks at 0, 25, 50, 75, 100 percent of the date range.
  * A filled area path from the curve down to the zero line, painted with a vertical linear gradient (`#plFill`) from `--color-primary-500` at 28 percent down to fully transparent.
  * The curve itself: 2 px primary stroke, round line caps and joins.
  * Y axis title rotated 90 degrees: `cum. P&L (USD)`.
* Axis text uses Newsreader 10 px tabular figures, fill `--color-text-muted`.

### Interactions

* Selecting a strategy or changing the date range regenerates the synthetic curve (in v1 the data is generated client side via a deterministic LCG seeded from the strategy name; Phase 10 replaces this with real backend output).
* Run backtest button is the only action; in v1 it is a noop because the curve is reactive to state.

## Screen 5: History

URL state: `active === 'history'`.

### Layout grid

* Single `[data-component="HistoryList"]` card with no internal padding so the table touches the card border.
* Card head: title `Calculation History`, meta `<N> entries`.

### Visible components

`[data-component="DataTable"]`: a standard HTML table.

* `<thead>`: ten columns: Time, Ticker, S, K, T, r, sigma, Call, Put, action. Numeric headers carry `data-element="numHeader"` for right alignment.
* `<tbody>`: each row is `[data-element="row"]`, clickable, `tabIndex="0"`. On hover the row gets a `surface-2` background. On focus it shows a 2 px primary inset outline.
* Cells: time and ticker use italic serif; numeric cells use `.t-num` (Newsreader, tabular). Call values use `.tr-pos`, put values `.tr-neg`. Last column is a small icon button (rotate-ccw) for "reload these inputs into the Pricing screen".

### Interactions

* Clicking a row (or pressing Enter on a focused row) calls `onLoad(row)`; the parent App writes the row's S, K, T, r, sigma into Pricing inputs and switches the active screen to Pricing.
* No sort, no filter, no pagination in v1. Phase 6 introduces persistence; this screen will then load from the backend.

## Design decisions (resolved with the user 2026-05-02)

The five questions raised during extraction were resolved with the user during the Phase 0 check-in. Frontend Developer should treat the answers below as authoritative starting in Phase 3.

1. **Heat map legend.** Ship a legend in v1. Add `[data-component="HeatMap"] [data-element="legend"]` showing the active color stops, sized to fit beside the heat map without crowding the cells.
2. **Light theme.** Light theme **is in scope for v1**. The Top bar moon icon is a working theme toggle, not a placeholder. The toggle persists the user's choice (localStorage). The canonical HTML is dark only, so a light variant of the Oxblood palette must be produced before Phase 3 starts; the production approach (Claude Design round trip versus deriving from the existing tokens) is a Phase 3 prep decision.
3. **Model selector interactivity.** Always show all three models (Black Scholes, binomial, Monte Carlo) side by side. No hide/show toggle in v1.
4. **History row action icon.** Keep the reload icon as is. Both the icon and the row click target remain valid entry points; intentional redundancy.
5. **Backtest "Run" button semantics.** Run is an explicit trigger. The chart is empty until the user clicks Run; reactive recomputation on input change is dropped from the v1 spec.
