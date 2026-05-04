/**
 * Top level Pricing screen: ticker autocomplete + model selector +
 * input form on the left, result panel on the right. Owns the form
 * state, the in flight controllers, the API calls, and the
 * single-vs-compare mode flag.
 *
 * In single mode the screen makes one POST /api/price call and
 * renders the call/put plus Greeks for the selected model. In
 * compare mode it fans out three parallel calls (one per model) and
 * renders the side by side ComparePanel; the Greeks panel still
 * shows the analytical Black Scholes Greeks because per project
 * convention Greeks come from the closed form regardless of model.
 */

import { useCallback, useRef, useState, type JSX } from 'react'

import { ComparePanel } from '../components/ComparePanel'
import { InputForm } from '../components/InputForm'
import { ModelSelector } from '../components/ModelSelector'
import { ResultPanel } from '../components/ResultPanel'
import { TickerAutocomplete } from '../components/TickerAutocomplete'
import {
  fetchPrice,
  PriceError,
  type PriceRequest,
  type PriceResponse,
  type PricingModel,
  type TickerQuote,
} from '../lib/api'

const INITIAL_INPUTS: PriceRequest = {
  S: 100,
  K: 100,
  T: 1,
  r: 0.05,
  sigma: 0.2,
}

const ALL_MODELS: PricingModel[] = ['black_scholes', 'binomial', 'monte_carlo']

type Status = { kind: 'idle' } | { kind: 'pending' } | { kind: 'error'; message: string }

type CompareResults = Record<PricingModel, PriceResponse | null>

const EMPTY_COMPARE: CompareResults = {
  black_scholes: null,
  binomial: null,
  monte_carlo: null,
}

interface PricingScreenProps {
  /**
   * Initial value for the Compare toggle. The dedicated "Model
   * Comparison" nav item lands the user with `initialCompare={true}`
   * so the side by side view shows up immediately. The toggle is
   * still on the screen so users can flip back to single mode.
   */
  initialCompare?: boolean
}

export function PricingScreen({ initialCompare = false }: PricingScreenProps = {}): JSX.Element {
  const [inputs, setInputs] = useState<PriceRequest>(INITIAL_INPUTS)
  const [model, setModel] = useState<PricingModel>('black_scholes')
  const [compare, setCompare] = useState<boolean>(initialCompare)
  const [result, setResult] = useState<PriceResponse | null>(null)
  const [compareResults, setCompareResults] = useState<CompareResults>(EMPTY_COMPARE)
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

    if (compare) {
      setCompareResults(EMPTY_COMPARE)
      const promises = ALL_MODELS.map((m) =>
        fetchPrice({ ...inputs, model: m }, { signal: controller.signal }).then(
          (res) => ({ ok: true as const, model: m, res }),
          (err: unknown) => ({ ok: false as const, model: m, err }),
        ),
      )
      const settled = await Promise.all(promises)
      if (controller.signal.aborted) return

      const next: CompareResults = { ...EMPTY_COMPARE }
      let firstError: PriceError | null = null
      for (const entry of settled) {
        if (entry.ok) {
          next[entry.model] = entry.res
        } else if (entry.err instanceof PriceError && firstError === null) {
          firstError = entry.err
        }
      }
      setCompareResults(next)
      if (firstError !== null) {
        if (firstError.kind === 'validation' && firstError.fields) {
          setInvalidFields(new Set(firstError.fields as ReadonlyArray<keyof PriceRequest>))
        }
        setStatus({ kind: 'error', message: firstError.message })
      } else {
        setStatus({ kind: 'idle' })
      }
      return
    }

    try {
      const response = await fetchPrice({ ...inputs, model }, { signal: controller.signal })
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
  }, [inputs, model, compare])

  const errorMessage = status.kind === 'error' ? status.message : ''
  const infoMessage = status.kind !== 'error' ? infoStatusMessage(status, compare, result) : ''

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
        <ModelSelector
          model={model}
          compare={compare}
          onModelChange={setModel}
          onCompareChange={setCompare}
        />
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
        {compare ? (
          <ComparePanel results={compareResults} pending={status.kind === 'pending'} />
        ) : (
          <ResultPanel inputs={inputs} result={result} />
        )}
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

function infoStatusMessage(status: Status, compare: boolean, result: PriceResponse | null): string {
  if (status.kind === 'pending') return compare ? 'Comparing models...' : 'Calculating...'
  if (compare) return 'Press Calculate to compare all three models.'
  if (result) return 'Pricing complete.'
  return 'Enter inputs and press Calculate.'
}

function round2(n: number): number {
  return Math.round(n * 100) / 100
}
