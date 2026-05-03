/**
 * Heat map controls card: mode tabs, vol shock range, spot shock
 * range, resolution selector, and (in P&L mode) the basis fields.
 *
 * Stateless: every value is owned by the parent ``HeatMapScreen``,
 * which serializes the controls into the request body for
 * ``POST /api/heatmap``.
 */

import type { JSX } from 'react'

import { Icon } from './Icon'
import { NumField } from './NumField'
import type { HeatMapMode } from './HeatMap'

export interface HeatMapControlsState {
  mode: HeatMapMode
  volShock: [number, number]
  spotShock: [number, number]
  resolution: number
  callBasis: number
  putBasis: number
}

interface HeatMapControlsProps {
  inputs: HeatMapControlsState
  pending: boolean
  onChange: (next: HeatMapControlsState) => void
  onRecompute: () => void
}

const RESOLUTIONS = [5, 9, 13, 17, 21] as const

export function HeatMapControls({
  inputs,
  pending,
  onChange,
  onRecompute,
}: HeatMapControlsProps): JSX.Element {
  const set = <K extends keyof HeatMapControlsState>(key: K, value: HeatMapControlsState[K]) =>
    onChange({ ...inputs, [key]: value })

  return (
    <section className="tr-card tr-heatmap-controls" data-component="HeatMapControls">
      <div className="tr-card-head">
        <h2 className="tr-card-title">Controls</h2>
        <span className="tr-card-meta">{inputs.mode === 'value' ? 'Value mode' : 'P&L mode'}</span>
      </div>
      <div role="tablist" data-component="Tabs" aria-label="Heat map mode">
        <button
          type="button"
          role="tab"
          data-element="tab"
          data-active={inputs.mode === 'value' ? 'true' : 'false'}
          aria-selected={inputs.mode === 'value'}
          onClick={() => set('mode', 'value')}
        >
          <Icon name="grid-3x3" size={14} /> Value
        </button>
        <button
          type="button"
          role="tab"
          data-element="tab"
          data-active={inputs.mode === 'pl' ? 'true' : 'false'}
          aria-selected={inputs.mode === 'pl'}
          onClick={() => set('mode', 'pl')}
        >
          <Icon name="trending-up" size={14} /> P&amp;L
        </button>
      </div>

      <div className="tr-control-grid">
        <RangeField
          label="Vol shock"
          values={inputs.volShock}
          min={-0.95}
          max={1.0}
          step={0.05}
          onChange={(next) => set('volShock', next)}
        />
        <RangeField
          label="Spot shock"
          values={inputs.spotShock}
          min={-0.5}
          max={0.5}
          step={0.025}
          onChange={(next) => set('spotShock', next)}
        />
        <div data-element="row">
          <label className="tr-label" htmlFor="hm-resolution">
            Resolution
          </label>
          <select
            id="hm-resolution"
            className="tr-input"
            value={inputs.resolution}
            onChange={(e) => set('resolution', Number(e.target.value))}
          >
            {RESOLUTIONS.map((r) => (
              <option key={r} value={r}>
                {r} x {r}
              </option>
            ))}
          </select>
        </div>
        {inputs.mode === 'pl' && (
          <>
            <NumField
              label="Call paid"
              suffix="USD"
              value={inputs.callBasis}
              min={0}
              onChange={(v) => set('callBasis', v)}
            />
            <NumField
              label="Put paid"
              suffix="USD"
              value={inputs.putBasis}
              min={0}
              onChange={(v) => set('putBasis', v)}
            />
          </>
        )}
      </div>

      <button
        type="button"
        className="tr-btn tr-btn--primary tr-calc-btn"
        disabled={pending}
        aria-busy={pending}
        onClick={onRecompute}
      >
        <Icon name="grid-3x3" size={16} />
        {pending ? 'Computing' : 'Recompute heat map'}
      </button>
    </section>
  )
}

interface RangeFieldProps {
  label: string
  values: [number, number]
  min: number
  max: number
  step: number
  onChange: (next: [number, number]) => void
}

function RangeField({ label, values, min, max, step, onChange }: RangeFieldProps): JSX.Element {
  const [lo, hi] = values
  return (
    <div data-element="row">
      <label className="tr-label">
        {label}{' '}
        <span className="t-num tr-range-vals">
          {Math.round(lo * 100)} to {Math.round(hi * 100)}%
        </span>
      </label>
      <div className="tr-range-pair">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={lo}
          aria-label={`${label} minimum`}
          onChange={(e) => onChange([+e.target.value, Math.max(+e.target.value, hi)])}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={hi}
          aria-label={`${label} maximum`}
          onChange={(e) => onChange([Math.min(+e.target.value, lo), +e.target.value])}
        />
      </div>
    </div>
  )
}
