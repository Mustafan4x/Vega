/**
 * Heat Map screen.
 *
 * Composes the controls card on top with two heat maps below (call,
 * put) painted from the response of ``POST /api/heatmap``. The screen
 * owns its own input state for the five Black Scholes parameters so
 * a user can iterate on the heat map without touching the Pricing
 * screen state in Phase 3.
 */

import { useCallback, useRef, useState, type JSX } from 'react'

import { HeatMap } from '../components/HeatMap'
import { HeatMapControls, type HeatMapControlsState } from '../components/HeatMapControls'
import { InputForm } from '../components/InputForm'
import { fetchHeatmap, PriceError, type HeatmapResponse, type PriceRequest } from '../lib/api'

const INITIAL_INPUTS: PriceRequest = {
  S: 100,
  K: 100,
  T: 1,
  r: 0.05,
  sigma: 0.2,
}

const INITIAL_CONTROLS: HeatMapControlsState = {
  mode: 'value',
  volShock: [-0.5, 0.5],
  spotShock: [-0.3, 0.3],
  resolution: 9,
  callBasis: 10,
  putBasis: 5,
}

type Status =
  | { kind: 'idle' }
  | { kind: 'pending' }
  | { kind: 'ready' }
  | { kind: 'error'; message: string }

export function HeatMapScreen(): JSX.Element {
  const [inputs, setInputs] = useState<PriceRequest>(INITIAL_INPUTS)
  const [controls, setControls] = useState<HeatMapControlsState>(INITIAL_CONTROLS)
  const [response, setResponse] = useState<HeatmapResponse | null>(null)
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [invalidFields, setInvalidFields] = useState<ReadonlySet<keyof PriceRequest>>(
    () => new Set(),
  )
  const inFlight = useRef<AbortController | null>(null)

  const onRecompute = useCallback(async () => {
    inFlight.current?.abort()
    const controller = new AbortController()
    inFlight.current = controller

    setStatus({ kind: 'pending' })
    setInvalidFields(new Set())

    try {
      const result = await fetchHeatmap(
        {
          ...inputs,
          vol_shock: controls.volShock,
          spot_shock: controls.spotShock,
          rows: controls.resolution,
          cols: controls.resolution,
        },
        { signal: controller.signal },
      )
      if (controller.signal.aborted) return
      setResponse(result)
      setStatus({ kind: 'ready' })
    } catch (err) {
      if (controller.signal.aborted) return
      if (err instanceof PriceError) {
        if (err.kind === 'validation' && err.fields) {
          setInvalidFields(new Set(err.fields as ReadonlyArray<keyof PriceRequest>))
        }
        setStatus({ kind: 'error', message: err.message })
        return
      }
      setStatus({ kind: 'error', message: 'Something went wrong computing the heat map.' })
    }
  }, [inputs, controls])

  const callGrid = response?.call ?? []
  const putGrid = response?.put ?? []
  const sigmaAxis = response?.sigma_axis ?? []
  const spotAxis = response?.spot_axis ?? []

  const errorMessage = status.kind === 'error' ? status.message : ''
  const infoMessage = status.kind === 'error' ? '' : statusMessage(status)

  return (
    <div className="tr-heatmap-screen tr-screen-fade" data-component="HeatMapScreen">
      <h1 className="sr-only">Heat Map</h1>
      <div className="tr-heatmap-top">
        <InputForm
          inputs={inputs}
          invalid={invalidFields}
          pending={status.kind === 'pending'}
          onChange={(next) => {
            setInputs(next)
            if (invalidFields.size > 0) setInvalidFields(new Set())
          }}
          onCalculate={onRecompute}
        />
        <HeatMapControls
          inputs={controls}
          pending={status.kind === 'pending'}
          onChange={setControls}
          onRecompute={onRecompute}
        />
      </div>

      <div className="tr-heatmap-grids">
        <HeatMap
          dataComp="HeatMap"
          title={controls.mode === 'value' ? 'Call value' : 'Call P&L'}
          grid={callGrid}
          vAxis={sigmaAxis}
          sAxis={spotAxis}
          mode={controls.mode}
          basis={controls.callBasis}
        />
        <HeatMap
          dataComp="PnlHeatMap"
          title={controls.mode === 'value' ? 'Put value' : 'Put P&L'}
          grid={putGrid}
          vAxis={sigmaAxis}
          sAxis={spotAxis}
          mode={controls.mode}
          basis={controls.putBasis}
        />
      </div>

      <p
        className="tr-status"
        role="status"
        aria-live="polite"
        aria-atomic="true"
        data-element="status"
      >
        {infoMessage}
      </p>
      <p className="tr-status tr-status--error" role="alert" data-element="error">
        {errorMessage}
      </p>
    </div>
  )
}

function statusMessage(status: Status): string {
  if (status.kind === 'pending') return 'Computing heat map...'
  if (status.kind === 'ready') return 'Heat map ready.'
  return 'Set inputs and shock ranges, then press Recompute.'
}
