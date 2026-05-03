import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchBacktest, PriceError, type BacktestRequest } from './api'

const REQUEST: BacktestRequest = {
  symbol: 'AAPL',
  strategy: 'long_call',
  start_date: '2026-01-02',
  end_date: '2026-02-15',
  sigma: 0.2,
  r: 0.05,
  dte_days: 30,
}
const BASE_URL = 'http://api.test'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('fetchBacktest', () => {
  const fetchSpy = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchSpy.mockReset()
    vi.stubGlobal('fetch', fetchSpy)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('parses a 200 into a BacktestResponse', async () => {
    fetchSpy.mockResolvedValue(
      jsonResponse(200, {
        symbol: 'AAPL',
        strategy: 'long_call',
        dates: ['2026-01-02', '2026-01-03'],
        spot: [100, 101],
        position_value: [3.0, 3.2],
        pnl: [0, 0.2],
        strike: 100,
        entry_basis: 3.0,
        entry_date: '2026-01-02',
        expiry_date: '2026-02-01',
        legs: [{ sign: 1, kind: 'call' }],
      }),
    )

    const result = await fetchBacktest(REQUEST, { baseUrl: BASE_URL })

    expect(result.symbol).toBe('AAPL')
    expect(result.dates).toHaveLength(2)
    expect(result.legs[0].kind).toBe('call')
  })

  it('uppercases the symbol before sending', async () => {
    fetchSpy.mockResolvedValue(
      jsonResponse(200, {
        symbol: 'AAPL',
        strategy: 'long_call',
        dates: ['2026-01-02'],
        spot: [100],
        position_value: [3.0],
        pnl: [0],
        strike: 100,
        entry_basis: 3.0,
        entry_date: '2026-01-02',
        expiry_date: '2026-02-01',
        legs: [{ sign: 1, kind: 'call' }],
      }),
    )

    await fetchBacktest({ ...REQUEST, symbol: 'aapl' }, { baseUrl: BASE_URL })

    const body = JSON.parse(fetchSpy.mock.calls[0][1]?.body as string)
    expect(body.symbol).toBe('AAPL')
  })

  it('rejects locally invalid symbols without calling fetch', async () => {
    await expect(
      fetchBacktest({ ...REQUEST, symbol: 'aapl!' }, { baseUrl: BASE_URL }),
    ).rejects.toMatchObject({ kind: 'validation' })
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('rejects an unexpected response shape with a server PriceError', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(200, { symbol: 'AAPL' }))

    await expect(fetchBacktest(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'server',
    })
  })

  it('maps 404 to not_found', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(404, { detail: 'Ticker not found.' }))
    await expect(fetchBacktest(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'not_found',
    })
  })

  it('maps 504 to upstream_timeout', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(504, { detail: 'Historical data lookup timed out.' }))
    await expect(fetchBacktest(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'upstream_timeout',
    })
  })

  it('maps 502 to upstream', async () => {
    fetchSpy.mockResolvedValue(
      jsonResponse(502, { detail: 'Historical data upstream unavailable.' }),
    )
    await expect(fetchBacktest(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'upstream',
    })
  })

  it('maps 422 to validation with field hints', async () => {
    fetchSpy.mockResolvedValue(
      jsonResponse(422, {
        detail: [{ loc: ['body', 'dte_days'], msg: 'too large', type: 'less_than_equal' }],
      }),
    )
    await expect(fetchBacktest(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'validation',
      fields: ['dte_days'],
    })
  })

  it('rejects with PriceError when fetch throws (network)', async () => {
    fetchSpy.mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(fetchBacktest(REQUEST, { baseUrl: BASE_URL })).rejects.toBeInstanceOf(PriceError)
  })
})
