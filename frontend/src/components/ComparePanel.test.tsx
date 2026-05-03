import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { ComparePanel } from './ComparePanel'
import type { PriceResponse } from '../lib/api'

function makeResult(model: PriceResponse['model'], call: number, put: number): PriceResponse {
  const greeks = {
    delta: 0.5,
    gamma: 0.01,
    theta_per_day: -0.02,
    vega_per_pct: 0.3,
    rho_per_pct: 0.4,
  }
  return { call, put, model, call_greeks: greeks, put_greeks: { ...greeks, delta: -0.5 } }
}

describe('ComparePanel', () => {
  it('renders the three model columns with their call and put values', () => {
    render(
      <ComparePanel
        results={{
          black_scholes: makeResult('black_scholes', 10.45, 5.57),
          binomial: makeResult('binomial', 10.46, 5.58),
          monte_carlo: makeResult('monte_carlo', 10.4, 5.55),
        }}
        pending={false}
      />,
    )

    expect(screen.getByText(/Black Scholes/i)).toBeInTheDocument()
    expect(screen.getByText(/Binomial/i)).toBeInTheDocument()
    expect(screen.getByText(/Monte Carlo/i)).toBeInTheDocument()
    // Call values
    expect(screen.getByText(/10\.45/)).toBeInTheDocument()
    expect(screen.getByText(/10\.46/)).toBeInTheDocument()
    expect(screen.getByText(/10\.40/)).toBeInTheDocument()
    // Put values
    expect(screen.getByText(/5\.57/)).toBeInTheDocument()
  })

  it('shows a placeholder when results are missing for a model', () => {
    render(
      <ComparePanel
        results={{
          black_scholes: makeResult('black_scholes', 10.45, 5.57),
          binomial: null,
          monte_carlo: null,
        }}
        pending={true}
      />,
    )

    // Should still render all three columns with at least one en dash
    // style placeholder for the empty cells.
    const placeholders = screen.getAllByText('...')
    expect(placeholders.length).toBeGreaterThanOrEqual(2)
  })

  it('flags the maximum spread across the three call values', () => {
    render(
      <ComparePanel
        results={{
          black_scholes: makeResult('black_scholes', 10.0, 5.0),
          binomial: makeResult('binomial', 10.1, 5.0),
          monte_carlo: makeResult('monte_carlo', 9.5, 5.0),
        }}
        pending={false}
      />,
    )

    // Spread is max - min = 10.1 - 9.5 = 0.6 across call values.
    expect(screen.getByText(/spread/i)).toBeInTheDocument()
    expect(screen.getByText(/0\.60/)).toBeInTheDocument()
  })
})
