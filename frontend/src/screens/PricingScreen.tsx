/**
 * Top level Pricing screen: input form on the left, result panel on the
 * right. Owns the form state, the in flight controller, and the API
 * call. Renders an inline status string when the request is pending,
 * cancelled, or failed.
 */

import { useCallback, useRef, useState, type JSX } from 'react'

import { InputForm } from '../components/InputForm'
import { ResultPanel } from '../components/ResultPanel'
import { TickerAutocomplete } from '../components/TickerAutocomplete'
import {
  fetchPrice,
  PriceError,
  type PriceRequest,
  type PriceResponse,
  type TickerQuote,
} from '../lib/api'

const INITIAL_INPUTS: PriceRequest = {
  S: 100,
  K: 100,
  T: 1,
  r: 0.05,
  sigma: 0.2,
}

type Status = { kind: 'idle' } | { kind: 'pending' } | { kind: 'error'; message: string }

export function PricingScreen(): JSX.Element {
  const [inputs, setInputs] = useState<PriceRequest>(INITIAL_INPUTS)
  const [result, setResult] = useState<PriceResponse | null>(null)
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [invalidFields, setInvalidFields] = useState<ReadonlySet<keyof PriceRequest>>(
    () => new Set(),
  )
  const inFlight = useRef<AbortController | null>(null)

  const onCalculate = useCallback(async () => {
    inFlight.current?.abort()
    const controller = new AbortController()
    inFlight.current = controller

    setStatus({ kind: 'pending' })
    setInvalidFields(new Set())

    try {
      const response = await fetchPrice(inputs, { signal: controller.signal })
      if (controller.signal.aborted) return
      setResult(response)
      setStatus({ kind: 'idle' })
    } catch (err) {
      if (controller.signal.aborted) return
      if (err instanceof PriceError) {
        if (err.kind === 'validation' && err.fields) {
          setInvalidFields(new Set(err.fields as ReadonlyArray<keyof PriceRequest>))
        }
        setStatus({ kind: 'error', message: err.message })
        return
      }
      setStatus({ kind: 'error', message: 'Something went wrong calculating the price.' })
    }
  }, [inputs])

  const errorMessage = status.kind === 'error' ? status.message : ''
  const infoMessage = status.kind !== 'error' ? infoStatusMessage(status, result) : ''

  const onTickerApply = useCallback((quote: TickerQuote) => {
    inFlight.current?.abort()
    setInputs((prev) => ({ ...prev, S: round2(quote.price) }))
    setStatus({ kind: 'idle' })
    setInvalidFields(new Set())
  }, [])

  return (
    <div className="tr-pricing tr-screen-fade" data-component="PricingScreen">
      <h1 className="sr-only">Pricing</h1>
      <div data-element="leftColumn">
        <TickerAutocomplete onApply={onTickerApply} />
        <InputForm
          inputs={inputs}
          invalid={invalidFields}
          pending={status.kind === 'pending'}
          onChange={(next) => {
            setInputs(next)
            if (invalidFields.size > 0) setInvalidFields(new Set())
          }}
          onCalculate={onCalculate}
        />
      </div>
      <div data-element="resultColumn">
        <ResultPanel inputs={inputs} result={result} />
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

function infoStatusMessage(status: Status, result: PriceResponse | null): string {
  if (status.kind === 'pending') return 'Calculating...'
  if (result) return 'Pricing complete.'
  return 'Enter inputs and press Calculate.'
}

function round2(n: number): number {
  return Math.round(n * 100) / 100
}
