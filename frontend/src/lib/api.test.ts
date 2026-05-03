import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

import { fetchPrice, PriceError, type PriceRequest } from './api'

const REQUEST: PriceRequest = { S: 100, K: 100, T: 1, r: 0.05, sigma: 0.2 }
const BASE_URL = 'http://api.test'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('fetchPrice', () => {
  const fetchSpy = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchSpy.mockReset()
    vi.stubGlobal('fetch', fetchSpy)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('parses a 200 response into a PriceResponse', async () => {
    const greeksFixture = {
      delta: 0.5,
      gamma: 0.01,
      theta_per_day: -0.02,
      vega_per_pct: 0.3,
      rho_per_pct: 0.4,
    }
    fetchSpy.mockResolvedValue(
      jsonResponse(200, {
        call: 10.45,
        put: 5.57,
        model: 'black_scholes',
        call_greeks: greeksFixture,
        put_greeks: { ...greeksFixture, delta: -0.5 },
      }),
    )

    const result = await fetchPrice(REQUEST, { baseUrl: BASE_URL })

    expect(result.call).toBe(10.45)
    expect(result.put).toBe(5.57)
    expect(result.call_greeks.delta).toBe(0.5)
    expect(result.put_greeks.delta).toBe(-0.5)
    expect(fetchSpy).toHaveBeenCalledWith(
      `${BASE_URL}/api/price`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(REQUEST),
      }),
    )
  })

  it('rejects a 200 response missing the greeks fields with a server PriceError', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(200, { call: 10.45, put: 5.57 }))

    await expect(fetchPrice(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'server',
    })
  })

  it('maps a 422 to a validation PriceError with the offending field names', async () => {
    fetchSpy.mockResolvedValue(
      jsonResponse(422, {
        detail: [
          { loc: ['body', 'S'], msg: 'must be positive', type: 'greater_than_equal' },
          { loc: ['body', 'sigma'], msg: 'must be positive', type: 'greater_than_equal' },
        ],
      }),
    )

    await expect(fetchPrice(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'validation',
      status: 422,
      fields: ['S', 'sigma'],
    })
  })

  it('maps a 429 to a rate_limit PriceError', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(429, { detail: 'Rate limit exceeded.' }))

    await expect(fetchPrice(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'rate_limit',
      status: 429,
    })
  })

  it('maps a 500 to a server PriceError', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(500, { detail: 'boom' }))

    await expect(fetchPrice(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'server',
      status: 500,
    })
  })

  it('maps a network failure to a network PriceError', async () => {
    fetchSpy.mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(fetchPrice(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'network',
    })
  })

  it('maps an external abort to an aborted PriceError', async () => {
    fetchSpy.mockImplementation(
      (_url, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () => {
            reject(Object.assign(new Error('aborted'), { name: 'AbortError' }))
          })
        }),
    )
    const controller = new AbortController()
    const promise = fetchPrice(REQUEST, { baseUrl: BASE_URL, signal: controller.signal })
    controller.abort()

    await expect(promise).rejects.toBeInstanceOf(PriceError)
    await expect(promise).rejects.toMatchObject({ kind: 'aborted' })
  })

  it('maps a deadline timeout to a timeout PriceError', async () => {
    fetchSpy.mockImplementation(
      (_url, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () => {
            reject(Object.assign(new Error('aborted'), { name: 'AbortError' }))
          })
        }),
    )

    await expect(fetchPrice(REQUEST, { baseUrl: BASE_URL, timeoutMs: 5 })).rejects.toMatchObject({
      kind: 'timeout',
    })
  })
})
