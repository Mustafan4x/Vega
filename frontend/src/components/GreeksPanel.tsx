/**
 * Greeks display panel: five tiles for delta, gamma, theta, vega, rho
 * for either the call or the put. Anatomy mirrors the canonical
 * reference at ``docs/design/claude-design-output.html`` lines 1330 to
 * 1350: each tile carries a glyph (Greek letter, italic serif), a
 * value (Newsreader, tabular), a name (italic serif body sm), and a
 * 3 px left accent border that cycles through five accents.
 *
 * The values come in display friendly units from the API:
 *
 *   delta:         dimensionless
 *   gamma:         per dollar of S
 *   theta_per_day: dollars per calendar day
 *   vega_per_pct:  dollars per 1 percent of sigma
 *   rho_per_pct:   dollars per 1 percent of r
 */

import type { JSX } from 'react'

import { fmtNumber, fmtUsd } from '../lib/format'
import type { GreeksDisplay } from '../lib/api'

interface GreeksPanelProps {
  title: string
  greeks: GreeksDisplay | null
}

interface TileSpec {
  glyph: string
  name: keyof GreeksDisplay | 'theta' | 'vega' | 'rho'
  label: string
  accent: 'primary' | 'accent' | 'amber' | 'info' | 'violet'
  format: (value: number) => string
}

const TILES: ReadonlyArray<TileSpec> = [
  {
    glyph: 'Δ',
    name: 'delta',
    label: 'Delta',
    accent: 'primary',
    format: (v) => fmtNumber(v, 4),
  },
  {
    glyph: 'Γ',
    name: 'gamma',
    label: 'Gamma',
    accent: 'accent',
    format: (v) => fmtNumber(v, 5),
  },
  {
    glyph: 'Θ',
    name: 'theta',
    label: 'Theta',
    accent: 'amber',
    format: (v) => fmtUsd(v, 4),
  },
  {
    glyph: 'ν',
    name: 'vega',
    label: 'Vega',
    accent: 'info',
    format: (v) => fmtUsd(v, 4),
  },
  {
    glyph: 'ρ',
    name: 'rho',
    label: 'Rho',
    accent: 'violet',
    format: (v) => fmtUsd(v, 4),
  },
]

function valueFor(greeks: GreeksDisplay, tile: TileSpec): number {
  switch (tile.name) {
    case 'delta':
      return greeks.delta
    case 'gamma':
      return greeks.gamma
    case 'theta':
      return greeks.theta_per_day
    case 'vega':
      return greeks.vega_per_pct
    case 'rho':
      return greeks.rho_per_pct
    default:
      return 0
  }
}

function ariaUnit(tile: TileSpec): string {
  switch (tile.name) {
    case 'theta':
      return 'per day'
    case 'vega':
      return 'per 1 percent of sigma'
    case 'rho':
      return 'per 1 percent of r'
    default:
      return ''
  }
}

export function GreeksPanel({ title, greeks }: GreeksPanelProps): JSX.Element {
  return (
    <section className="tr-card" data-component="GreeksPanel">
      <div className="tr-card-head">
        <h3 className="tr-card-title">{title}</h3>
        <span className="tr-card-meta">Per share</span>
      </div>
      <div data-element="row">
        {TILES.map((tile) => {
          const value = greeks ? valueFor(greeks, tile) : Number.NaN
          const formatted = greeks ? tile.format(value) : '—'
          const ariaLabel = greeks
            ? `${tile.label} ${formatted}${ariaUnit(tile) ? ' ' + ariaUnit(tile) : ''}`
            : `${tile.label} not yet computed`
          return (
            <div
              key={tile.name}
              data-element="tile"
              data-accent={tile.accent}
              role="group"
              aria-label={ariaLabel}
            >
              <div data-element="glyph" aria-hidden="true">
                {tile.glyph}
              </div>
              <div className="t-num" data-element="value">
                {formatted}
              </div>
              <div data-element="name">{tile.label}</div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
