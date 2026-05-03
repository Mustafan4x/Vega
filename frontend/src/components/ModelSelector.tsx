/**
 * Pricing model selector: three tabs (Black Scholes, Binomial, Monte
 * Carlo) plus a Compare toggle. Selecting a tab routes the next
 * /api/price call through that pricer; flipping Compare on disables
 * the tabs and tells the parent to fan out to all three models in
 * parallel.
 *
 * Stateless: the model and the compare flag are owned by the parent
 * (PricingScreen), which serializes them into the API requests.
 */

import type { JSX } from 'react'

import type { PricingModel } from '../lib/api'

interface ModelSelectorProps {
  model: PricingModel
  compare: boolean
  onModelChange: (next: PricingModel) => void
  onCompareChange: (next: boolean) => void
}

const MODELS: { id: PricingModel; label: string; short: string }[] = [
  { id: 'black_scholes', label: 'Black Scholes', short: 'BS' },
  { id: 'binomial', label: 'Binomial', short: 'CRR' },
  { id: 'monte_carlo', label: 'Monte Carlo', short: 'MC' },
]

export function ModelSelector({
  model,
  compare,
  onModelChange,
  onCompareChange,
}: ModelSelectorProps): JSX.Element {
  return (
    <section className="tr-card" data-component="ModelSelector">
      <div className="tr-card-head">
        <h2 className="tr-card-title">Model</h2>
        <span className="tr-card-meta">pricer</span>
      </div>
      <div role="tablist" aria-label="Pricing model" data-element="tabs">
        {MODELS.map(({ id, label, short }) => {
          const selected = model === id && !compare
          return (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={selected}
              disabled={compare}
              className={`tr-tab${selected ? ' tr-tab--active' : ''}`}
              onClick={() => onModelChange(id)}
              data-element="tab"
              data-model={id}
            >
              <span className="tr-tab-label">{label}</span>
              <span className="tr-tab-short tr-mono" aria-hidden="true">
                {short}
              </span>
            </button>
          )
        })}
      </div>
      <div data-element="compareRow">
        <label className="tr-toggle">
          <button
            type="button"
            role="switch"
            aria-checked={compare}
            aria-label="Compare all three models"
            className={`tr-toggle-track${compare ? ' tr-toggle-track--on' : ''}`}
            onClick={() => onCompareChange(!compare)}
            data-element="compareToggle"
          >
            <span className="tr-toggle-thumb" aria-hidden="true" />
          </button>
          <span className="tr-toggle-label">Compare all models</span>
        </label>
      </div>
    </section>
  )
}
