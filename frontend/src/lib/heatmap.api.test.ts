import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchHeatmap, type HeatmapRequest } from './api'

const REQUEST: HeatmapRequest = {
  S: 100,
  K: 100,
  T: 1,
  r: 0.05,
  sigma: 0.2,
  vol_shock: [-0.5, 0.5],
  spot_shock: [-0.3, 0.3],
  rows: 9,
  cols: 9,
}
const BASE_URL = 'http://api.test'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('fetchHeatmap', () => {
  const fetchSpy = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchSpy.mockReset()
    vi.stubGlobal('fetch', fetchSpy)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('parses a 200 into a HeatmapResponse', async () => {
    const grid = [
      [1, 2],
      [3, 4],
    ]
    fetchSpy.mockResolvedValue(
      jsonResponse(200, {
        call: grid,
        put: grid,
        sigma_axis: [0.1, 0.2],
        spot_axis: [70, 130],
      }),
    )

    const result = await fetchHeatmap(REQUEST, { baseUrl: BASE_URL })

    expect(result.call).toEqual(grid)
    expect(result.sigma_axis).toEqual([0.1, 0.2])
    expect(fetchSpy).toHaveBeenCalledWith(
      `${BASE_URL}/api/heatmap`,
      expect.objectContaining({ method: 'POST', body: JSON.stringify(REQUEST) }),
    )
  })

  it('rejects an unexpected response shape with a server PriceError', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(200, { call: 'nope' }))

    await expect(fetchHeatmap(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'server',
    })
  })

  it('maps a 422 to a validation PriceError with offending fields', async () => {
    fetchSpy.mockResolvedValue(
      jsonResponse(422, {
        detail: [{ loc: ['body', 'rows'], msg: 'too large', type: 'less_than_equal' }],
      }),
    )

    await expect(fetchHeatmap(REQUEST, { baseUrl: BASE_URL })).rejects.toMatchObject({
      kind: 'validation',
      fields: ['rows'],
    })
  })
})
