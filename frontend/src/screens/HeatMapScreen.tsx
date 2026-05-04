/**
 * Heat Map screen.
 *
 * Composes the controls card on top with two heat maps below (call,
 * put) painted from the response of ``POST /api/heatmap``. The screen
 * owns its own input state for the five Black Scholes parameters so
 * a user can iterate on the heat map without touching the Pricing
 * screen state.
 *
 * The Save button (Phase 11) calls ``POST /api/calculations`` with the
 * same payload so the History screen can list and reload it.
 */

import { useCallback, useRef, useState, type JSX } from 'react'
import { useAuth0 } from '@auth0/auth0-react'

import { HeatMap } from '../components/HeatMap'
import { HeatMapControls, type HeatMapControlsState } from '../components/HeatMapControls'
import { InputForm } from '../components/InputForm'
import {
  fetchHeatmap,
  PriceError,
  saveCalculation,
  type HeatmapRequest,
  type HeatmapResponse,
  type PriceRequest,
} from '../lib/api'

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

type SaveStatus =
  | { kind: 'idle' }
  | { kind: 'saving' }
  | { kind: 'saved'; calculationId: string }
  | { kind: 'error'; message: string }

export function HeatMapScreen(): JSX.Element {
  const { isAuthenticated, getAccessTokenSilently, loginWithRedirect } = useAuth0()
  const [inputs, setInputs] = useState<PriceRequest>(INITIAL_INPUTS)
  const [controls, setControls] = useState<HeatMapControlsState>(INITIAL_CONTROLS)
  const [response, setResponse] = useState<HeatmapResponse | null>(null)
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [saveStatus, setSaveStatus] = useState<SaveStatus>({ kind: 'idle' })
  const [invalidFields, setInvalidFields] = useState<ReadonlySet<keyof PriceRequest>>(
    () => new Set(),
  )
  const inFlight = useRef<AbortController | null>(null)
  const inFlightSave = useRef<AbortController | null>(null)

  const onRecompute = useCallback(async () => {
    inFlight.current?.abort()
    const controller = new AbortController()
    inFlight.current = controller

    setStatus({ kind: 'pending' })
    setInvalidFields(new Set())
    // A new compute invalidates the previous "saved" badge.
    setSaveStatus({ kind: 'idle' })

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

  const onSave = useCallback(async () => {
    if (response === null) return
    const request: HeatmapRequest = {
      ...inputs,
      vol_shock: controls.volShock,
      spot_shock: controls.spotShock,
      rows: controls.resolution,
      cols: controls.resolution,
    }
    if (!isAuthenticated) {
      await loginWithRedirect({
        appState: { pendingSave: { request } },
      })
      return
    }
    inFlightSave.current?.abort()
    const controller = new AbortController()
    inFlightSave.current = controller
    setSaveStatus({ kind: 'saving' })
    try {
      const token = await getAccessTokenSilently()
      const result = await saveCalculation(request, {
        signal: controller.signal,
        bearerToken: token,
      })
      if (controller.signal.aborted) return
      setSaveStatus({ kind: 'saved', calculationId: result.calculation_id })
    } catch (err) {
      if (controller.signal.aborted) return
      const message = err instanceof PriceError ? err.message : 'Could not save the calculation.'
      setSaveStatus({ kind: 'error', message })
    }
  }, [inputs, controls, response, isAuthenticated, getAccessTokenSilently, loginWithRedirect])

  const callGrid = response?.call ?? []
  const putGrid = response?.put ?? []
  const sigmaAxis = response?.sigma_axis ?? []
  const spotAxis = response?.spot_axis ?? []

  const errorMessage = status.kind === 'error' ? status.message : ''
  const infoMessage = status.kind === 'error' ? '' : statusMessage(status)

  const canSave = status.kind === 'ready' && saveStatus.kind !== 'saving' && response !== null
  const saveLabel = !isAuthenticated
    ? 'Sign in to save'
    : saveStatus.kind === 'saving'
      ? 'Saving...'
      : saveStatus.kind === 'saved'
        ? 'Saved'
        : 'Save'
  const saveFeedback = saveStatusMessage(saveStatus)

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

      <div className="tr-heatmap-actions" data-element="actions">
        <button
          type="button"
          className="tr-btn"
          data-element="saveButton"
          onClick={onSave}
          disabled={!canSave}
          aria-busy={saveStatus.kind === 'saving'}
        >
          {saveLabel}
        </button>
        <span className="tr-status" data-element="saveStatus" aria-live="polite">
          {saveFeedback}
        </span>
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

function saveStatusMessage(saveStatus: SaveStatus): string {
  if (saveStatus.kind === 'saving') return 'Saving to history...'
  if (saveStatus.kind === 'saved') return 'Saved. Open History to revisit.'
  if (saveStatus.kind === 'error') return saveStatus.message
  return ''
}
