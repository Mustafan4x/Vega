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
