/**
 * Backtest input form: ticker, strategy, date range, DTE, sigma, r.
 *
 * Stateless: parent owns the request shape and passes it back via
 * onChange. The Run button triggers the backtest fetch in the
 * parent screen.
 */

import { useId, type JSX } from 'react'

import { Icon } from './Icon'
import { NumField } from './NumField'
import type { BacktestRequest, BacktestStrategy } from '../lib/api'

const STRATEGIES: { id: BacktestStrategy; label: string }[] = [
  { id: 'long_call', label: 'Long Call' },
  { id: 'long_put', label: 'Long Put' },
  { id: 'straddle', label: 'Straddle' },
]

interface BacktestFormProps {
  inputs: BacktestRequest
  invalid: ReadonlySet<keyof BacktestRequest>
  pending: boolean
  onChange: (next: BacktestRequest) => void
  onRun: () => void
}

export function BacktestForm({
  inputs,
  invalid,
  pending,
  onChange,
  onRun,
}: BacktestFormProps): JSX.Element {
  const symbolId = useId()
  const strategyId = useId()
  const startId = useId()
  const endId = useId()

  const set = <K extends keyof BacktestRequest>(key: K, value: BacktestRequest[K]) => {
    onChange({ ...inputs, [key]: value })
  }

  return (
    <section className="tr-card" data-component="BacktestForm">
      <div className="tr-card-head">
        <h2 className="tr-card-title">Backtest</h2>
        <span className="tr-card-meta">historical replay</span>
      </div>
      <form
        data-element="grid"
        onSubmit={(e) => {
          e.preventDefault()
          onRun()
        }}
      >
        <div data-element="row">
          <label className="tr-label" htmlFor={symbolId}>
            Ticker symbol
          </label>
          <div className="tr-input-wrap">
            <input
              id={symbolId}
              type="text"
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="characters"
              spellCheck={false}
              maxLength={10}
              placeholder="AAPL"
              className="tr-input tr-mono"
              value={inputs.symbol}
              aria-invalid={invalid.has('symbol')}
              onChange={(e) => set('symbol', e.target.value.toUpperCase())}
            />
          </div>
        </div>

        <div data-element="row">
          <label className="tr-label" htmlFor={strategyId}>
            Strategy
          </label>
          <select
            id={strategyId}
            className="tr-input"
            value={inputs.strategy}
            aria-invalid={invalid.has('strategy')}
            onChange={(e) => set('strategy', e.target.value as BacktestStrategy)}
          >
            {STRATEGIES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div data-element="row">
          <label className="tr-label" htmlFor={startId}>
            Start date
          </label>
          <div className="tr-input-wrap">
            <input
              id={startId}
              type="date"
              className="tr-input tr-mono"
              value={inputs.start_date}
              aria-invalid={invalid.has('start_date')}
              onChange={(e) => set('start_date', e.target.value)}
            />
          </div>
        </div>

        <div data-element="row">
          <label className="tr-label" htmlFor={endId}>
            End date
          </label>
          <div className="tr-input-wrap">
            <input
              id={endId}
              type="date"
              className="tr-input tr-mono"
              value={inputs.end_date}
              aria-invalid={invalid.has('end_date')}
              onChange={(e) => set('end_date', e.target.value)}
            />
          </div>
        </div>

        <NumField
          label="Days to expiry"
          suffix="days"
          value={inputs.dte_days}
          min={1}
          invalid={invalid.has('dte_days')}
          onChange={(v) => set('dte_days', Math.round(v))}
        />
        <NumField
          label="Implied volatility"
          suffix="%"
          value={Number((inputs.sigma * 100).toFixed(3))}
          min={0}
          invalid={invalid.has('sigma')}
          onChange={(v) => set('sigma', v / 100)}
        />
        <NumField
          label="Risk free rate"
          suffix="%"
          value={Number((inputs.r * 100).toFixed(3))}
          invalid={invalid.has('r')}
          onChange={(v) => set('r', v / 100)}
        />

        <button
          type="submit"
          className="tr-btn tr-btn--primary tr-calc-btn"
          disabled={pending}
          aria-busy={pending}
        >
          <Icon name="activity" size={16} />
          {pending ? 'Running' : 'Run backtest'}
        </button>
      </form>
    </section>
  )
}
