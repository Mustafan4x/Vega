/**
 * Pricing inputs card: the five Black Scholes parameters plus the
 * Calculate button. Renders the field for ``r`` and ``sigma`` in
 * percent (more familiar for users) and converts to/from decimal at
 * the boundary so the API client always sees the canonical units.
 *
 * The component is presentational: state and the submit handler are
 * owned by the parent (``PricingScreen``), which talks to the API.
 */

import type { JSX } from 'react'

import { Icon } from './Icon'
import { NumField } from './NumField'
import type { PriceRequest } from '../lib/api'

interface InputFormProps {
  inputs: PriceRequest
  invalid: ReadonlySet<keyof PriceRequest>
  pending: boolean
  onChange: (next: PriceRequest) => void
  onCalculate: () => void
}

export function InputForm({
  inputs,
  invalid,
  pending,
  onChange,
  onCalculate,
}: InputFormProps): JSX.Element {
  const setField = <K extends keyof PriceRequest>(key: K, value: number) => {
    onChange({ ...inputs, [key]: value })
  }

  return (
    <section className="tr-card" data-component="InputForm">
      <div className="tr-card-head">
        <h2 className="tr-card-title">Inputs</h2>
        <span className="tr-card-meta">Black Scholes</span>
      </div>
      <form
        data-element="grid"
        onSubmit={(e) => {
          e.preventDefault()
          onCalculate()
        }}
      >
        <NumField
          label="Asset Price (S)"
          suffix="USD"
          value={inputs.S}
          min={0}
          invalid={invalid.has('S')}
          onChange={(v) => setField('S', v)}
        />
        <NumField
          label="Strike (K)"
          suffix="USD"
          value={inputs.K}
          min={0}
          invalid={invalid.has('K')}
          onChange={(v) => setField('K', v)}
        />
        <NumField
          label="Time to Expiry (T)"
          suffix="yrs"
          value={inputs.T}
          min={0}
          invalid={invalid.has('T')}
          onChange={(v) => setField('T', v)}
        />
        <NumField
          label="Risk Free Rate (r)"
          suffix="%"
          value={Number((inputs.r * 100).toFixed(3))}
          invalid={invalid.has('r')}
          onChange={(v) => setField('r', v / 100)}
        />
        <NumField
          label="Volatility (sigma)"
          suffix="%"
          value={Number((inputs.sigma * 100).toFixed(3))}
          min={0}
          invalid={invalid.has('sigma')}
          onChange={(v) => setField('sigma', v / 100)}
        />
        <button
          type="submit"
          className="tr-btn tr-btn--primary tr-calc-btn"
          disabled={pending}
          aria-busy={pending}
        >
          <Icon name="calculator" size={16} />
          {pending ? 'Calculating' : 'Calculate'}
        </button>
      </form>
    </section>
  )
}
