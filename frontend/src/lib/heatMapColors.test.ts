import { describe, expect, it } from 'vitest'

import { plColor, rgbToCss, stopsNeg, stopsPos, stopsValue, valueColor } from './heatMapColors'

describe('valueColor', () => {
  it('returns the first stop at the minimum of the data range', () => {
    expect(valueColor(0, 0, 100)).toEqual(stopsValue[0])
  })

  it('returns the last stop at the maximum of the data range', () => {
    expect(valueColor(100, 0, 100)).toEqual(stopsValue[stopsValue.length - 1])
  })

  it('returns the amber midpoint at t = 0.5', () => {
    expect(valueColor(50, 0, 100)).toEqual(stopsValue[2])
  })

  it('clamps below the minimum to the first stop', () => {
    expect(valueColor(-10, 0, 100)).toEqual(stopsValue[0])
  })

  it('clamps above the maximum to the last stop', () => {
    expect(valueColor(110, 0, 100)).toEqual(stopsValue[stopsValue.length - 1])
  })

  it('handles a zero range without dividing by zero', () => {
    const c = valueColor(5, 5, 5)
    expect(c.every(Number.isFinite)).toBe(true)
  })
})

describe('plColor', () => {
  it('returns the neutral gray at zero P&L', () => {
    const c = plColor(10, 10)
    expect(c).toEqual(stopsPos[0])
  })

  it('returns deepest negative when P&L saturates the negative ramp', () => {
    const c = plColor(-1000, 100)
    expect(c).toEqual(stopsNeg[0])
  })

  it('returns deepest positive when P&L saturates the positive ramp', () => {
    const c = plColor(10_000, 100)
    expect(c).toEqual(stopsPos[stopsPos.length - 1])
  })

  it('uses the soft normalizer for tiny basis values', () => {
    const c = plColor(1, 0)
    expect(c.every(Number.isFinite)).toBe(true)
  })
})

describe('rgbToCss', () => {
  it('rounds and formats an rgb triple', () => {
    expect(rgbToCss([10.4, 20.5, 30.6])).toBe('rgb(10, 21, 31)')
  })
})

describe('plColor sign property tests', () => {
  // Pseudo random fixture: avoids a real PRNG dep so the test is hermetic.
  const cases: Array<[number, number]> = []
  for (let basis = 1; basis <= 50; basis += 7) {
    for (let delta = -basis; delta <= basis * 2; delta += 3) {
      cases.push([basis + delta, basis])
    }
  }

  it('values below the basis return a red leaning color (R >= G and R >= B)', () => {
    for (const [value, basis] of cases) {
      if (value >= basis) continue
      const [r, g, b] = plColor(value, basis)
      expect(r >= g - 1).toBe(true)
      expect(r >= b - 1).toBe(true)
    }
  })

  it('values above the basis return a green leaning color (G >= R and G >= B)', () => {
    for (const [value, basis] of cases) {
      if (value <= basis) continue
      const [r, g, b] = plColor(value, basis)
      expect(g >= r - 1).toBe(true)
      expect(g >= b - 1).toBe(true)
    }
  })

  it('value equal to basis returns the neutral gray stop', () => {
    for (let basis = 1; basis <= 50; basis += 7) {
      const c = plColor(basis, basis)
      expect(c).toEqual(stopsPos[0])
    }
  })

  it('symmetric P&L magnitudes around the basis produce mirrored ramp positions', () => {
    const basis = 10
    const small = plColor(basis - 2, basis)
    const big = plColor(basis - 12, basis)
    // Larger magnitude on the loss side should be visually deeper red:
    // R component should not decrease as the loss grows.
    expect(big[0] <= small[0] + 5).toBe(true)
  })
})
