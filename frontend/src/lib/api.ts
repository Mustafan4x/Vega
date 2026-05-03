/**
 * Typed API client for the Trader backend.
 *
 * Wraps `POST /api/price` with strict request and response types, an
 * AbortController plus deadline so the UI never hangs on a slow backend,
 * and an error normalization step that maps validation errors, timeouts,
 * rate limiting, and network failures to a small `PriceError` union the
 * UI can render without leaking backend internals.
 */

const DEFAULT_BASE_URL = 'http://localhost:8000'
const DEFAULT_TIMEOUT_MS = 8_000

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

interface FetchPriceOptions {
  baseUrl?: string
  timeoutMs?: number
  signal?: AbortSignal
}

interface ValidationDetail {
  loc?: ReadonlyArray<string | number>
  msg?: string
  type?: string
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

export async function fetchPrice(
  request: PriceRequest,
  options: FetchPriceOptions = {},
): Promise<PriceResponse> {
  const baseUrl = trimTrailingSlash(options.baseUrl ?? readApiBaseUrl())
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const controller = new AbortController()
  combineSignals(options.signal, controller)
  const timer = setTimeout(() => controller.abort(new Error('timeout')), timeoutMs)

  let response: Response
  try {
    response = await fetch(`${baseUrl}/api/price`, {
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
        throw new PriceError('timeout', 'The pricing request timed out.')
      }
      throw new PriceError('aborted', 'The pricing request was cancelled.')
    }
    throw new PriceError('network', 'Could not reach the pricing service.')
  }
  clearTimeout(timer)

  if (response.status === 200) {
    const body = (await response.json()) as PriceResponse
    if (typeof body?.call !== 'number' || typeof body?.put !== 'number') {
      throw new PriceError('server', 'Unexpected response shape from the pricing service.', {
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

  throw new PriceError('server', `The pricing service returned ${response.status}.`, {
    status: response.status,
  })
}
