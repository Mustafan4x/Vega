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

export interface PriceRequest {
  S: number
  K: number
  T: number
  r: number
  sigma: number
}

export interface PriceResponse {
  call: number
  put: number
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
  return import.meta.env?.VITE_API_BASE_URL ?? DEFAULT_BASE_URL
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

function isPriceResponse(body: unknown): body is PriceResponse {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  return typeof b.call === 'number' && typeof b.put === 'number'
}

function isHeatmapResponse(body: unknown): body is HeatmapResponse {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  return (
    Array.isArray(b.call) &&
    Array.isArray(b.put) &&
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
