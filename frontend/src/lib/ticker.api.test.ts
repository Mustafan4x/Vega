import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchTicker, PriceError } from './api'

const BASE_URL = 'http://api.test'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('fetchTicker', () => {
  const fetchSpy = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchSpy.mockReset()
    vi.stubGlobal('fetch', fetchSpy)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('parses a 200 into a TickerQuote', async () => {
    fetchSpy.mockResolvedValue(
      jsonResponse(200, {
        symbol: 'AAPL',
        name: 'Apple Inc.',
        price: 199.5,
        currency: 'USD',
      }),
    )

    const result = await fetchTicker('AAPL', { baseUrl: BASE_URL })

    expect(result).toEqual({
      symbol: 'AAPL',
      name: 'Apple Inc.',
      price: 199.5,
      currency: 'USD',
    })
    expect(fetchSpy).toHaveBeenCalledWith(
      `${BASE_URL}/api/tickers/AAPL`,
      expect.objectContaining({ method: 'GET', credentials: 'omit', mode: 'cors' }),
    )
  })

  it('uppercases the symbol before requesting', async () => {
    fetchSpy.mockResolvedValue(
      jsonResponse(200, { symbol: 'AAPL', name: 'Apple Inc.', price: 1, currency: 'USD' }),
    )

    await fetchTicker('aapl', { baseUrl: BASE_URL })

    expect(fetchSpy).toHaveBeenCalledWith(
      `${BASE_URL}/api/tickers/AAPL`,
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('rejects an unexpected response shape with a server PriceError', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(200, { symbol: 'AAPL' }))

    await expect(fetchTicker('AAPL', { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'server',
    })
  })

  it('maps 404 to a not_found PriceError without leaking', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(404, { detail: 'Ticker not found.' }))

    await expect(fetchTicker('ZZZZ', { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'not_found',
      status: 404,
    })
  })

  it('maps 504 to an upstream_timeout PriceError', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(504, { detail: 'Ticker lookup timed out.' }))

    await expect(fetchTicker('AAPL', { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'upstream_timeout',
      status: 504,
    })
  })

  it('maps 502 to an upstream PriceError', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(502, { detail: 'Ticker upstream unavailable.' }))

    await expect(fetchTicker('AAPL', { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'upstream',
      status: 502,
    })
  })

  it('rejects locally invalid symbols as validation without status', async () => {
    await expect(fetchTicker('aapl!', { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'validation',
    })
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('maps a server 422 (defence in depth) to validation', async () => {
    fetchSpy.mockResolvedValue(
      jsonResponse(422, {
        detail: [{ loc: ['path', 'symbol'], msg: 'invalid', type: 'string_pattern_mismatch' }],
      }),
    )

    await expect(fetchTicker('AAPL', { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'validation',
      status: 422,
    })
  })

  it('rejects with PriceError when fetch throws (network)', async () => {
    fetchSpy.mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(fetchTicker('AAPL', { baseUrl: BASE_URL })).rejects.toBeInstanceOf(PriceError)
  })

  it('rejects empty / blank symbols without calling fetch', async () => {
    await expect(fetchTicker('', { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'validation',
    })
    await expect(fetchTicker('  ', { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'validation',
    })
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})
