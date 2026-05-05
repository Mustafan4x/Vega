/**
 * Backtest screen: input form on the left, P&L chart on the right.
 * Owns the form state, the in flight controller, and the API call.
 * Renders an inline status string and an error region for failures.
 */

import { useCallback, useRef, useState, type JSX } from 'react'

import { BacktestChart } from '../components/BacktestChart'
import { BacktestForm } from '../components/BacktestForm'
import { fetchBacktest, PriceError, type BacktestRequest, type BacktestResponse } from '../lib/api'

const INITIAL_INPUTS: BacktestRequest = {
  symbol: 'AAPL',
  strategy: 'long_call',
  start_date: defaultStart(),
  end_date: defaultEnd(),
  sigma: 0.2,
  r: 0.05,
  q: 0,
  dte_days: 30,
}

type Status = { kind: 'idle' } | { kind: 'pending' } | { kind: 'error'; message: string }

export function BacktestScreen(): JSX.Element {
  const [inputs, setInputs] = useState<BacktestRequest>(INITIAL_INPUTS)
  const [result, setResult] = useState<BacktestResponse | null>(null)
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [invalidFields, setInvalidFields] = useState<ReadonlySet<keyof BacktestRequest>>(
    () => new Set(),
  )
  const inFlight = useRef<AbortController | null>(null)

  const onRun = useCallback(async () => {
    inFlight.current?.abort()
    const controller = new AbortController()
    inFlight.current = controller

    setStatus({ kind: 'pending' })
    setInvalidFields(new Set())

    try {
      const response = await fetchBacktest(inputs, { signal: controller.signal })
      if (controller.signal.aborted) return
      setResult(response)
      setStatus({ kind: 'idle' })
    } catch (err) {
      if (controller.signal.aborted) return
      if (err instanceof PriceError) {
        if (err.kind === 'validation' && err.fields) {
          setInvalidFields(new Set(err.fields as ReadonlyArray<keyof BacktestRequest>))
        }
        setStatus({ kind: 'error', message: err.message })
        return
      }
      setStatus({ kind: 'error', message: 'Something went wrong running the backtest.' })
    }
  }, [inputs])

  const errorMessage = status.kind === 'error' ? status.message : ''
  const infoMessage = status.kind !== 'error' ? infoStatusMessage(status, result) : ''

  return (
    <div className="tr-backtest tr-screen-fade" data-component="BacktestScreen">
      <h1 className="sr-only">Backtest</h1>
      <BacktestForm
        inputs={inputs}
        invalid={invalidFields}
        pending={status.kind === 'pending'}
        onChange={(next) => {
          setInputs(next)
          if (invalidFields.size > 0) setInvalidFields(new Set())
        }}
        onRun={onRun}
      />
      <div data-element="resultColumn">
        <BacktestChart result={result} />
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
    </div>
  )
}

function infoStatusMessage(status: Status, result: BacktestResponse | null): string {
  if (status.kind === 'pending') return 'Replaying history...'
  if (result) return `Backtest complete: ${result.dates.length} days replayed.`
  return 'Pick a symbol, strategy, and date range, then press Run backtest.'
}

function defaultStart(): string {
  const d = new Date()
  d.setMonth(d.getMonth() - 3)
  return d.toISOString().slice(0, 10)
}

function defaultEnd(): string {
  const d = new Date()
  return d.toISOString().slice(0, 10)
}
