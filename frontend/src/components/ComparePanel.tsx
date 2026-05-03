/**
 * Side by side comparison of the three pricing models.
 *
 * Each column shows one model's call and put. The header row reports
 * the largest call-side spread across the three models, which is the
 * single number that tells a user "do my models agree?". Loading
 * cells render an ellipsis placeholder so the layout does not jump
 * when one of the three responses arrives later than the others.
 */

import type { JSX } from 'react'

import type { PriceResponse, PricingModel } from '../lib/api'

const MODEL_LABELS: Record<PricingModel, string> = {
  black_scholes: 'Black Scholes',
  binomial: 'Binomial',
  monte_carlo: 'Monte Carlo',
}

const MODEL_ORDER: PricingModel[] = ['black_scholes', 'binomial', 'monte_carlo']

interface ComparePanelProps {
  results: Record<PricingModel, PriceResponse | null>
  pending: boolean
}

export function ComparePanel({ results, pending }: ComparePanelProps): JSX.Element {
  const calls = MODEL_ORDER.map((m) => results[m]?.call).filter(
    (v): v is number => typeof v === 'number',
  )
  const spread =
    calls.length === MODEL_ORDER.length ? Math.max(...calls) - Math.min(...calls) : null

  return (
    <section className="tr-card" data-component="ComparePanel">
      <div className="tr-card-head">
        <h2 className="tr-card-title">Compare</h2>
        <span className="tr-card-meta" data-element="spreadBadge">
          {spread === null ? (pending ? 'computing' : '') : `Call spread $${spread.toFixed(2)}`}
        </span>
      </div>
      <div data-element="columns">
        {MODEL_ORDER.map((model) => {
          const r = results[model]
          return (
            <div key={model} data-element="column" data-model={model}>
              <div className="tr-compare-head">{MODEL_LABELS[model]}</div>
              <Row label="Call" value={r?.call} />
              <Row label="Put" value={r?.put} />
            </div>
          )
        })}
      </div>
    </section>
  )
}

interface RowProps {
  label: string
  value: number | undefined
}

function Row({ label, value }: RowProps): JSX.Element {
  return (
    <div className="tr-compare-row">
      <span className="tr-compare-label">{label}</span>
      <span className="tr-compare-value tr-mono">
        {typeof value === 'number' ? `$${value.toFixed(2)}` : '...'}
      </span>
    </div>
  )
}
