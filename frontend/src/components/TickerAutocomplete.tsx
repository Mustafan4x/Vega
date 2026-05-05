/**
 * Ticker symbol autocomplete: debounced lookup against
 * ``GET /api/tickers/{symbol}``. The user types a symbol; after 250ms
 * of inactivity we resolve a quote and surface a "Use price" button.
 * Clicking the button calls ``onApply`` with the full quote so the
 * parent can wire the price into its form.
 *
 * Focus opens a dropdown of popular tickers; clicking one fills the
 * input and triggers the lookup. Filter narrows as the user types.
 *
 * The component is intentionally explicit (resolve, then click): the
 * threat model lists market data as untrusted, and silently
 * overwriting the user's price field on every keystroke would make
 * a typo destructive.
 */

import { useCallback, useEffect, useId, useMemo, useRef, useState, type JSX } from 'react'

import { Icon } from './Icon'
import { fetchTicker, PriceError, type TickerQuote } from '../lib/api'
import sp500Data from '../data/sp500.json'

const DEBOUNCE_MS = 250
const TICKER_RE = /^[A-Z0-9.-]{1,10}$/
const MAX_RESULTS = 12

interface TickerEntry {
  symbol: string
  name: string
}

const SP500: ReadonlyArray<TickerEntry> = sp500Data as ReadonlyArray<TickerEntry>

// Curated headliner set shown before the user starts typing. Once they
// type anything, the full S&P 500 universe is searched.
const POPULAR_SYMBOLS = [
  'AAPL',
  'MSFT',
  'GOOGL',
  'AMZN',
  'NVDA',
  'TSLA',
  'META',
  'JPM',
  'V',
  'WMT',
  'HD',
  'DIS',
] as const

const POPULAR_TICKERS: ReadonlyArray<TickerEntry> = POPULAR_SYMBOLS.flatMap((s) => {
  const match = SP500.find((t) => t.symbol === s)
  return match ? [match] : []
})

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
  const listboxId = useId()
  const [draft, setDraft] = useState<string>('')
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false)
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
        setDropdownOpen(false)
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
      setDropdownOpen(true)
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

  const selectTicker = useCallback(
    (symbol: string) => {
      const upper = symbol.toUpperCase()
      setDraft(upper)
      setDropdownOpen(false)
      cancelInFlight()
      runLookup(upper)
    },
    [cancelInFlight, runLookup],
  )

  const onApplyClick = () => {
    if (status.kind === 'resolved') {
      onApply(status.quote)
    }
  }

  const filtered = useMemo(() => filterTickers(draft), [draft])

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
        <div className="tr-ticker-combo" data-element="combo">
          <div className="tr-input-wrap">
            <input
              id={inputId}
              type="search"
              role="combobox"
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
              aria-controls={listboxId}
              aria-expanded={dropdownOpen}
              aria-autocomplete="list"
              aria-haspopup="listbox"
              onChange={(e) => onInput(e.target.value)}
              onFocus={() => setDropdownOpen(true)}
              onBlur={() => {
                window.setTimeout(() => setDropdownOpen(false), 120)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  setDropdownOpen(false)
                }
              }}
            />
          </div>
          {dropdownOpen && filtered.length > 0 && (
            <ul
              id={listboxId}
              role="listbox"
              aria-label="Popular tickers"
              className="tr-ticker-listbox"
              data-element="listbox"
            >
              {filtered.map((entry) => (
                <li key={entry.symbol} role="presentation">
                  <button
                    type="button"
                    role="option"
                    aria-selected={draft === entry.symbol}
                    className="tr-ticker-option"
                    data-element="option"
                    title={`${entry.symbol}: ${entry.name}`}
                    onMouseDown={(e) => {
                      e.preventDefault()
                      selectTicker(entry.symbol)
                    }}
                  >
                    <span className="tr-mono" data-element="optionSymbol">
                      {entry.symbol}
                    </span>
                    <span data-element="optionName">{entry.name}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
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

function filterTickers(query: string): ReadonlyArray<TickerEntry> {
  const trimmed = query.trim()
  if (trimmed === '') return POPULAR_TICKERS
  const lower = trimmed.toLowerCase()

  // Symbol prefix matches rank above name substring matches; otherwise
  // a search like "A" buries AAPL under every name starting with A.
  const symbolPrefix: TickerEntry[] = []
  const symbolContains: TickerEntry[] = []
  const nameContains: TickerEntry[] = []

  for (const entry of SP500) {
    const sym = entry.symbol.toLowerCase()
    const name = entry.name.toLowerCase()
    if (sym.startsWith(lower)) {
      symbolPrefix.push(entry)
    } else if (sym.includes(lower)) {
      symbolContains.push(entry)
    } else if (name.includes(lower)) {
      nameContains.push(entry)
    }
    if (symbolPrefix.length >= MAX_RESULTS) break
  }

  return [...symbolPrefix, ...symbolContains, ...nameContains].slice(0, MAX_RESULTS)
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
