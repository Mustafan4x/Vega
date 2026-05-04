/**
 * Typed API client for the Trader backend.
 *
 * Wraps `POST /api/price` and `POST /api/heatmap` with strict request
 * and response types, an AbortController plus deadline so the UI never
 * hangs on a slow backend, and an error normalization step that maps
 * validation errors, timeouts, rate limiting, and network failures to
 * a single `PriceError` union the UI can render without leaking
 * backend internals.
 */

const DEFAULT_BASE_URL = 'http://localhost:8000'
const DEFAULT_TIMEOUT_MS = 8_000
const DEFAULT_HEATMAP_TIMEOUT_MS = 12_000
const DEFAULT_TICKER_TIMEOUT_MS = 6_000
const DEFAULT_BACKTEST_TIMEOUT_MS = 20_000

const TICKER_RE = /^[A-Z0-9.-]{1,10}$/

export type PricingModel = 'black_scholes' | 'binomial' | 'monte_carlo'

export interface PriceRequest {
  S: number
  K: number
  T: number
  r: number
  sigma: number
  model?: PricingModel
}

export interface GreeksDisplay {
  delta: number
  gamma: number
  theta_per_day: number
  vega_per_pct: number
  rho_per_pct: number
}

export interface PriceResponse {
  call: number
  put: number
  model: PricingModel
  call_greeks: GreeksDisplay
  put_greeks: GreeksDisplay
}

export interface HeatmapRequest extends PriceRequest {
  vol_shock: [number, number]
  spot_shock: [number, number]
  rows: number
  cols: number
}

export interface HeatmapResponse {
  call: number[][]
  put: number[][]
  model: PricingModel
  sigma_axis: number[]
  spot_axis: number[]
}

export interface TickerQuote {
  symbol: string
  name: string
  price: number
  currency: string
}

export type BacktestStrategy = 'long_call' | 'long_put' | 'straddle'

export interface BacktestRequest {
  symbol: string
  strategy: BacktestStrategy
  start_date: string
  end_date: string
  sigma: number
  r: number
  dte_days: number
}

export interface BacktestLeg {
  sign: number
  kind: string
}

export interface BacktestResponse {
  symbol: string
  strategy: BacktestStrategy
  dates: string[]
  spot: number[]
  position_value: number[]
  pnl: number[]
  strike: number
  entry_basis: number
  entry_date: string
  expiry_date: string
  legs: BacktestLeg[]
}

// Persistence (Phase 6 backend, Phase 11 frontend wiring).

export interface CalculationCreateResponse extends HeatmapResponse {
  calculation_id: string
}

export interface CalculationSummary {
  calculation_id: string
  created_at: string
  s: number
  k: number
  t: number
  r: number
  sigma: number
  rows: number
  cols: number
}

export interface CalculationListResponse {
  items: CalculationSummary[]
  total: number
  limit: number
  offset: number
}

export interface CalculationDetail {
  calculation_id: string
  s: number
  k: number
  t: number
  r: number
  sigma: number
  rows: number
  cols: number
  call: number[][]
  put: number[][]
  sigma_axis: number[]
  spot_axis: number[]
}

export type PriceErrorKind =
  | 'validation'
  | 'rate_limit'
  | 'server'
  | 'network'
  | 'timeout'
  | 'aborted'
  | 'not_found'
  | 'upstream_timeout'
  | 'upstream'

export class PriceError extends Error {
  readonly kind: PriceErrorKind
  readonly status?: number
  readonly fields?: ReadonlyArray<string>

  constructor(
    kind: PriceErrorKind,
    message: string,
    options: { status?: number; fields?: ReadonlyArray<string> } = {},
  ) {
    super(message)
    this.name = 'PriceError'
    this.kind = kind
    this.status = options.status
    this.fields = options.fields
  }
}

interface FetchOptions {
  baseUrl?: string
  timeoutMs?: number
  signal?: AbortSignal
}

interface ValidationDetail {
  loc?: ReadonlyArray<string | number>
  msg?: string
  type?: string
}

interface PostShape {
  path: string
  label: string
  defaultTimeoutMs: number
}

function readApiBaseUrl(): string {
  const env = import.meta.env ?? {}
  const explicit = typeof env.VITE_API_BASE_URL === 'string' ? env.VITE_API_BASE_URL.trim() : ''
  // Production fail loud: a production bundle without VITE_API_BASE_URL
  // means the deploy step forgot to wire the env var. Falling back to
  // localhost would hand every user a silently broken UI; throw at the
  // first request so the cause is obvious in the console. Cloudflare
  // Pages takes the env var at build time, so this check fires the
  // moment the broken bundle runs.
  if (env.PROD) {
    if (explicit === '') {
      throw new Error(
        'VITE_API_BASE_URL is not set. Production builds require an explicit ' +
          'backend URL; see docs/setup-guide.md (Cloudflare Pages env vars).',
      )
    }
    if (explicit.startsWith('http://localhost') || explicit.startsWith('http://127.')) {
      throw new Error(
        `VITE_API_BASE_URL=${explicit} is not allowed in a production build. ` +
          'Set it to the public Render backend URL.',
      )
    }
  }
  return explicit !== '' ? explicit : DEFAULT_BASE_URL
}

function trimTrailingSlash(url: string): string {
  return url.endsWith('/') ? url.slice(0, -1) : url
}

function combineSignals(signal: AbortSignal | undefined, controller: AbortController): void {
  if (!signal) return
  if (signal.aborted) {
    controller.abort(signal.reason)
    return
  }
  signal.addEventListener('abort', () => controller.abort(signal.reason), { once: true })
}

function extractValidationFields(detail: unknown): ReadonlyArray<string> {
  if (!Array.isArray(detail)) return []
  const fields: string[] = []
  for (const entry of detail as ValidationDetail[]) {
    const loc = entry?.loc
    if (Array.isArray(loc) && loc.length > 0) {
      const last = loc[loc.length - 1]
      if (typeof last === 'string') fields.push(last)
    }
  }
  return fields
}

async function postJson<TRequest, TResponse>(
  shape: PostShape,
  request: TRequest,
  options: FetchOptions,
  validate: (body: unknown) => body is TResponse,
): Promise<TResponse> {
  const baseUrl = trimTrailingSlash(options.baseUrl ?? readApiBaseUrl())
  const timeoutMs = options.timeoutMs ?? shape.defaultTimeoutMs
  const controller = new AbortController()
  combineSignals(options.signal, controller)
  const timer = setTimeout(() => controller.abort(new Error('timeout')), timeoutMs)

  let response: Response
  try {
    response = await fetch(`${baseUrl}${shape.path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(request),
      credentials: 'omit',
      mode: 'cors',
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timer)
    const isAbort =
      (err instanceof DOMException && err.name === 'AbortError') ||
      (err instanceof Error && err.name === 'AbortError') ||
      controller.signal.aborted
    if (isAbort) {
      const reason = controller.signal.reason
      if (reason instanceof Error && reason.message === 'timeout') {
        throw new PriceError('timeout', `The ${shape.label} request timed out.`)
      }
      throw new PriceError('aborted', `The ${shape.label} request was cancelled.`)
    }
    throw new PriceError('network', `Could not reach the ${shape.label} service.`)
  }
  clearTimeout(timer)

  if (response.status === 200) {
    const body = (await response.json()) as unknown
    if (!validate(body)) {
      throw new PriceError('server', `Unexpected response shape from the ${shape.label} service.`, {
        status: response.status,
      })
    }
    return body
  }

  if (response.status === 422) {
    const body = (await response.json().catch(() => ({}))) as { detail?: unknown }
    return Promise.reject(
      new PriceError('validation', 'One or more inputs are invalid.', {
        status: 422,
        fields: extractValidationFields(body.detail),
      }),
    )
  }

  if (response.status === 429) {
    throw new PriceError('rate_limit', 'Rate limit reached. Slow down and try again.', {
      status: 429,
    })
  }

  throw new PriceError('server', `The ${shape.label} service returned ${response.status}.`, {
    status: response.status,
  })
}

function isGreeksDisplay(g: unknown): g is GreeksDisplay {
  if (typeof g !== 'object' || g === null) return false
  const r = g as Record<string, unknown>
  return (
    typeof r.delta === 'number' &&
    typeof r.gamma === 'number' &&
    typeof r.theta_per_day === 'number' &&
    typeof r.vega_per_pct === 'number' &&
    typeof r.rho_per_pct === 'number'
  )
}

function isPricingModel(value: unknown): value is PricingModel {
  return value === 'black_scholes' || value === 'binomial' || value === 'monte_carlo'
}

function isPriceResponse(body: unknown): body is PriceResponse {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  return (
    typeof b.call === 'number' &&
    typeof b.put === 'number' &&
    isPricingModel(b.model) &&
    isGreeksDisplay(b.call_greeks) &&
    isGreeksDisplay(b.put_greeks)
  )
}

function isHeatmapResponse(body: unknown): body is HeatmapResponse {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  return (
    Array.isArray(b.call) &&
    Array.isArray(b.put) &&
    isPricingModel(b.model) &&
    Array.isArray(b.sigma_axis) &&
    Array.isArray(b.spot_axis)
  )
}

export async function fetchPrice(
  request: PriceRequest,
  options: FetchOptions = {},
): Promise<PriceResponse> {
  return postJson<PriceRequest, PriceResponse>(
    { path: '/api/price', label: 'pricing', defaultTimeoutMs: DEFAULT_TIMEOUT_MS },
    request,
    options,
    isPriceResponse,
  )
}

export async function fetchHeatmap(
  request: HeatmapRequest,
  options: FetchOptions = {},
): Promise<HeatmapResponse> {
  return postJson<HeatmapRequest, HeatmapResponse>(
    { path: '/api/heatmap', label: 'heat map', defaultTimeoutMs: DEFAULT_HEATMAP_TIMEOUT_MS },
    request,
    options,
    isHeatmapResponse,
  )
}

function isTickerQuote(body: unknown): body is TickerQuote {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  return (
    typeof b.symbol === 'string' &&
    typeof b.name === 'string' &&
    typeof b.price === 'number' &&
    Number.isFinite(b.price) &&
    b.price > 0 &&
    typeof b.currency === 'string'
  )
}

export async function fetchTicker(
  rawSymbol: string,
  options: FetchOptions = {},
): Promise<TickerQuote> {
  const symbol = rawSymbol.trim().toUpperCase()
  if (!TICKER_RE.test(symbol)) {
    throw new PriceError('validation', 'Symbol must be 1 to 10 letters, digits, dots, or dashes.')
  }
  const baseUrl = trimTrailingSlash(options.baseUrl ?? readApiBaseUrl())
  const timeoutMs = options.timeoutMs ?? DEFAULT_TICKER_TIMEOUT_MS
  const controller = new AbortController()
  combineSignals(options.signal, controller)
  const timer = setTimeout(() => controller.abort(new Error('timeout')), timeoutMs)

  let response: Response
  try {
    response = await fetch(`${baseUrl}/api/tickers/${encodeURIComponent(symbol)}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      credentials: 'omit',
      mode: 'cors',
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timer)
    const isAbort =
      (err instanceof DOMException && err.name === 'AbortError') ||
      (err instanceof Error && err.name === 'AbortError') ||
      controller.signal.aborted
    if (isAbort) {
      const reason = controller.signal.reason
      if (reason instanceof Error && reason.message === 'timeout') {
        throw new PriceError('timeout', 'The ticker lookup timed out.')
      }
      throw new PriceError('aborted', 'The ticker lookup was cancelled.')
    }
    throw new PriceError('network', 'Could not reach the ticker service.')
  }
  clearTimeout(timer)

  if (response.status === 200) {
    const body = (await response.json()) as unknown
    if (!isTickerQuote(body)) {
      throw new PriceError('server', 'Unexpected response shape from the ticker service.', {
        status: 200,
      })
    }
    return body
  }

  if (response.status === 404) {
    throw new PriceError('not_found', 'No data for that symbol.', { status: 404 })
  }
  if (response.status === 422) {
    const body = (await response.json().catch(() => ({}))) as { detail?: unknown }
    throw new PriceError('validation', 'Symbol is not a valid ticker.', {
      status: 422,
      fields: extractValidationFields(body.detail),
    })
  }
  if (response.status === 429) {
    throw new PriceError('rate_limit', 'Rate limit reached. Slow down and try again.', {
      status: 429,
    })
  }
  if (response.status === 504) {
    throw new PriceError('upstream_timeout', 'The market data provider timed out.', {
      status: 504,
    })
  }
  if (response.status === 502 || response.status === 503) {
    throw new PriceError('upstream', 'Market data is unavailable right now.', {
      status: response.status,
    })
  }

  throw new PriceError('server', `The ticker service returned ${response.status}.`, {
    status: response.status,
  })
}

function isBacktestResponse(body: unknown): body is BacktestResponse {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  return (
    typeof b.symbol === 'string' &&
    typeof b.strategy === 'string' &&
    Array.isArray(b.dates) &&
    Array.isArray(b.spot) &&
    Array.isArray(b.position_value) &&
    Array.isArray(b.pnl) &&
    typeof b.strike === 'number' &&
    typeof b.entry_basis === 'number' &&
    typeof b.entry_date === 'string' &&
    typeof b.expiry_date === 'string' &&
    Array.isArray(b.legs)
  )
}

export async function fetchBacktest(
  request: BacktestRequest,
  options: FetchOptions = {},
): Promise<BacktestResponse> {
  if (!TICKER_RE.test(request.symbol.toUpperCase())) {
    throw new PriceError('validation', 'Symbol must be 1 to 10 letters, digits, dots, or dashes.')
  }
  const baseUrl = trimTrailingSlash(options.baseUrl ?? readApiBaseUrl())
  const timeoutMs = options.timeoutMs ?? DEFAULT_BACKTEST_TIMEOUT_MS
  const controller = new AbortController()
  combineSignals(options.signal, controller)
  const timer = setTimeout(() => controller.abort(new Error('timeout')), timeoutMs)

  let response: Response
  try {
    response = await fetch(`${baseUrl}/api/backtest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ ...request, symbol: request.symbol.toUpperCase() }),
      credentials: 'omit',
      mode: 'cors',
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timer)
    const isAbort =
      (err instanceof DOMException && err.name === 'AbortError') ||
      (err instanceof Error && err.name === 'AbortError') ||
      controller.signal.aborted
    if (isAbort) {
      const reason = controller.signal.reason
      if (reason instanceof Error && reason.message === 'timeout') {
        throw new PriceError('timeout', 'The backtest request timed out.')
      }
      throw new PriceError('aborted', 'The backtest request was cancelled.')
    }
    throw new PriceError('network', 'Could not reach the backtest service.')
  }
  clearTimeout(timer)

  if (response.status === 200) {
    const body = (await response.json()) as unknown
    if (!isBacktestResponse(body)) {
      throw new PriceError('server', 'Unexpected response shape from the backtest service.', {
        status: 200,
      })
    }
    return body
  }
  if (response.status === 404) {
    throw new PriceError('not_found', 'No data for that symbol.', { status: 404 })
  }
  if (response.status === 422) {
    const body = (await response.json().catch(() => ({}))) as { detail?: unknown }
    throw new PriceError('validation', 'One or more inputs are invalid.', {
      status: 422,
      fields: extractValidationFields(body.detail),
    })
  }
  if (response.status === 429) {
    throw new PriceError('rate_limit', 'Rate limit reached. Slow down and try again.', {
      status: 429,
    })
  }
  if (response.status === 504) {
    throw new PriceError('upstream_timeout', 'The market data provider timed out.', {
      status: 504,
    })
  }
  if (response.status === 502 || response.status === 503) {
    throw new PriceError('upstream', 'Historical market data is unavailable right now.', {
      status: response.status,
    })
  }

  throw new PriceError('server', `The backtest service returned ${response.status}.`, {
    status: response.status,
  })
}

// ---------- Calculations (persistence) ---------------------------------------

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/

function isCalculationCreateResponse(body: unknown): body is CalculationCreateResponse {
  if (!isHeatmapResponse(body)) return false
  const b = body as unknown as Record<string, unknown>
  return typeof b.calculation_id === 'string' && UUID_RE.test(b.calculation_id)
}

function isCalculationSummary(body: unknown): body is CalculationSummary {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  return (
    typeof b.calculation_id === 'string' &&
    typeof b.created_at === 'string' &&
    typeof b.s === 'number' &&
    typeof b.k === 'number' &&
    typeof b.t === 'number' &&
    typeof b.r === 'number' &&
    typeof b.sigma === 'number' &&
    typeof b.rows === 'number' &&
    typeof b.cols === 'number'
  )
}

function isCalculationListResponse(body: unknown): body is CalculationListResponse {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  if (typeof b.total !== 'number' || typeof b.limit !== 'number' || typeof b.offset !== 'number') {
    return false
  }
  return Array.isArray(b.items) && b.items.every(isCalculationSummary)
}

function isCalculationDetail(body: unknown): body is CalculationDetail {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  return (
    typeof b.calculation_id === 'string' &&
    typeof b.s === 'number' &&
    typeof b.k === 'number' &&
    typeof b.t === 'number' &&
    typeof b.r === 'number' &&
    typeof b.sigma === 'number' &&
    typeof b.rows === 'number' &&
    typeof b.cols === 'number' &&
    Array.isArray(b.call) &&
    Array.isArray(b.put) &&
    Array.isArray(b.sigma_axis) &&
    Array.isArray(b.spot_axis)
  )
}

export async function saveCalculation(
  request: HeatmapRequest,
  options: FetchOptions = {},
): Promise<CalculationCreateResponse> {
  return postJson<HeatmapRequest, CalculationCreateResponse>(
    {
      path: '/api/calculations',
      label: 'save calculation',
      defaultTimeoutMs: DEFAULT_HEATMAP_TIMEOUT_MS,
    },
    request,
    options,
    isCalculationCreateResponse,
  )
}

export interface ListCalculationsOptions extends FetchOptions {
  limit?: number
  offset?: number
}

async function getJson<TResponse>(
  path: string,
  label: string,
  defaultTimeoutMs: number,
  options: FetchOptions,
  validate: (body: unknown) => body is TResponse,
): Promise<TResponse> {
  const baseUrl = trimTrailingSlash(options.baseUrl ?? readApiBaseUrl())
  const timeoutMs = options.timeoutMs ?? defaultTimeoutMs
  const controller = new AbortController()
  combineSignals(options.signal, controller)
  const timer = setTimeout(() => controller.abort(new Error('timeout')), timeoutMs)

  let response: Response
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      credentials: 'omit',
      mode: 'cors',
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timer)
    const isAbort =
      (err instanceof DOMException && err.name === 'AbortError') ||
      (err instanceof Error && err.name === 'AbortError') ||
      controller.signal.aborted
    if (isAbort) {
      const reason = controller.signal.reason
      if (reason instanceof Error && reason.message === 'timeout') {
        throw new PriceError('timeout', `The ${label} request timed out.`)
      }
      throw new PriceError('aborted', `The ${label} request was cancelled.`)
    }
    throw new PriceError('network', `Could not reach the ${label} service.`)
  }
  clearTimeout(timer)

  if (response.status === 200) {
    const body = (await response.json()) as unknown
    if (!validate(body)) {
      throw new PriceError('server', `Unexpected response shape from ${label}.`, { status: 200 })
    }
    return body
  }
  if (response.status === 404) {
    throw new PriceError('not_found', 'Calculation not found.', { status: 404 })
  }
  if (response.status === 422) {
    throw new PriceError('validation', 'Invalid request parameters.', { status: 422 })
  }
  if (response.status === 429) {
    throw new PriceError('rate_limit', 'Rate limit reached. Slow down and try again.', {
      status: 429,
    })
  }
  throw new PriceError('server', `The ${label} service returned ${response.status}.`, {
    status: response.status,
  })
}

export async function fetchCalculations(
  options: ListCalculationsOptions = {},
): Promise<CalculationListResponse> {
  const params = new URLSearchParams()
  if (typeof options.limit === 'number') params.set('limit', String(options.limit))
  if (typeof options.offset === 'number') params.set('offset', String(options.offset))
  const qs = params.toString()
  const path = qs.length > 0 ? `/api/calculations?${qs}` : '/api/calculations'
  return getJson<CalculationListResponse>(
    path,
    'calculations list',
    DEFAULT_TIMEOUT_MS,
    options,
    isCalculationListResponse,
  )
}

export async function fetchCalculation(
  id: string,
  options: FetchOptions = {},
): Promise<CalculationDetail> {
  if (!UUID_RE.test(id)) {
    throw new PriceError('validation', 'Invalid calculation id.')
  }
  return getJson<CalculationDetail>(
    `/api/calculations/${encodeURIComponent(id)}`,
    'calculation detail',
    DEFAULT_TIMEOUT_MS,
    options,
    isCalculationDetail,
  )
}
