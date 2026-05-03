/**
 * Ticker symbol autocomplete: debounced lookup against
 * ``GET /api/tickers/{symbol}``. The user types a symbol; after 250ms
 * of inactivity we resolve a quote and surface a "Use price" button.
 * Clicking the button calls ``onApply`` with the full quote so the
 * parent can wire the price into its form.
 *
 * The component is intentionally explicit (resolve, then click): the
 * threat model lists market data as untrusted, and silently
 * overwriting the user's price field on every keystroke would make
 * a typo destructive.
 */

import { useCallback, useEffect, useId, useRef, useState, type JSX } from 'react'

import { Icon } from './Icon'
import { fetchTicker, PriceError, type TickerQuote } from '../lib/api'

const DEBOUNCE_MS = 250
const TICKER_RE = /^[A-Z0-9.-]{1,10}$/

interface TickerAutocompleteProps {
  onApply: (quote: TickerQuote) => void
}

type Status =
  | { kind: 'idle' }
  | { kind: 'pending'; symbol: string }
  | { kind: 'resolved'; quote: TickerQuote }
  | { kind: 'error'; message: string }

export function TickerAutocomplete({ onApply }: TickerAutocompleteProps): JSX.Element {
  const inputId = useId()
  const helpId = useId()
  const [draft, setDraft] = useState<string>('')
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const inFlight = useRef<AbortController | null>(null)
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const cancelInFlight = useCallback(() => {
    inFlight.current?.abort()
    inFlight.current = null
    if (debounceTimer.current !== null) {
      clearTimeout(debounceTimer.current)
      debounceTimer.current = null
    }
  }, [])

  useEffect(() => () => cancelInFlight(), [cancelInFlight])

  const runLookup = useCallback((symbol: string) => {
    const controller = new AbortController()
    inFlight.current = controller
    setStatus({ kind: 'pending', symbol })

    fetchTicker(symbol, { signal: controller.signal })
      .then((quote) => {
        if (controller.signal.aborted) return
        setStatus({ kind: 'resolved', quote })
      })
      .catch((err) => {
        if (controller.signal.aborted) return
        if (err instanceof PriceError) {
          setStatus({ kind: 'error', message: messageFor(err) })
        } else {
          setStatus({ kind: 'error', message: 'Could not look up that symbol.' })
        }
      })
  }, [])

  const onInput = useCallback(
    (raw: string) => {
      const next = raw.toUpperCase()
      setDraft(next)
      cancelInFlight()
      if (next === '') {
        setStatus({ kind: 'idle' })
        return
      }
      if (!TICKER_RE.test(next)) {
        setStatus({
          kind: 'error',
          message: 'Symbol must be 1 to 10 letters, digits, dots, or dashes.',
        })
        return
      }
      debounceTimer.current = setTimeout(() => {
        debounceTimer.current = null
        runLookup(next)
      }, DEBOUNCE_MS)
    },
    [cancelInFlight, runLookup],
  )

  const onApplyClick = () => {
    if (status.kind === 'resolved') {
      onApply(status.quote)
    }
  }

  return (
    <section className="tr-card" data-component="TickerAutocomplete">
      <div className="tr-card-head">
        <h2 className="tr-card-title">Market data</h2>
        <span className="tr-card-meta">yfinance</span>
      </div>
      <div data-element="search">
        <label className="tr-label" htmlFor={inputId}>
          Ticker symbol
        </label>
        <div className="tr-input-wrap">
          <input
            id={inputId}
            type="search"
            role="searchbox"
            inputMode="text"
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="characters"
            spellCheck={false}
            maxLength={10}
            placeholder="e.g. AAPL"
            className="tr-input tr-mono"
            value={draft}
            aria-describedby={helpId}
            onChange={(e) => onInput(e.target.value)}
          />
        </div>
        <p id={helpId} className="tr-status" data-element="hint">
          Look up the current price for a ticker.
        </p>
      </div>

      <div data-element="result">
        {status.kind === 'pending' && (
          <p className="tr-status" role="status" aria-live="polite" data-element="status">
            Looking up {status.symbol}...
          </p>
        )}
        {status.kind === 'resolved' && (
          <div data-element="quote">
            <div data-element="quoteLine">
              <span className="tr-mono" data-element="symbol">
                {status.quote.symbol}
              </span>
              <span data-element="name">{status.quote.name}</span>
              <span className="tr-mono" data-element="price">
                {formatPrice(status.quote.price, status.quote.currency)}
              </span>
            </div>
            <button
              type="button"
              className="tr-btn tr-btn--primary"
              onClick={onApplyClick}
              data-element="apply"
            >
              <Icon name="trending-up" size={16} />
              Use price
            </button>
          </div>
        )}
        {status.kind === 'error' && (
          <p className="tr-status tr-status--error" role="alert" data-element="error">
            {status.message}
          </p>
        )}
      </div>
    </section>
  )
}

function messageFor(err: PriceError): string {
  switch (err.kind) {
    case 'not_found':
      return 'No data for that symbol.'
    case 'validation':
      return 'Symbol is not a valid ticker.'
    case 'upstream_timeout':
      return 'Market data provider timed out. Try again.'
    case 'upstream':
      return 'Market data is unavailable right now.'
    case 'rate_limit':
      return 'Too many lookups. Wait a moment and try again.'
    case 'timeout':
      return 'Lookup timed out.'
    case 'aborted':
      return ''
    case 'network':
      return 'Could not reach the ticker service.'
    default:
      return err.message
  }
}

function formatPrice(price: number, currency: string): string {
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format(price)
  } catch {
    return `${currency} ${price.toFixed(2)}`
  }
}
