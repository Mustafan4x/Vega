import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

import { ResultColumn } from './ResultColumn'
import type { GreeksDisplay, PriceResponse } from '../lib/api'

const ATM_INPUTS = { S: 100, K: 100, T: 1, r: 0.05, sigma: 0.2 }
const ITM_CALL_INPUTS = { S: 110, K: 100, T: 1, r: 0.05, sigma: 0.2 }

const ZERO_GREEKS: GreeksDisplay = {
  delta: 0,
  gamma: 0,
  theta_per_day: 0,
  vega_per_pct: 0,
  rho_per_pct: 0,
  psi_per_pct: 0,
}

function priceResponse(call: number, put: number): PriceResponse {
  return {
    call,
    put,
    model: 'black_scholes',
    call_greeks: { ...ZERO_GREEKS, delta: 0.6368 },
    put_greeks: { ...ZERO_GREEKS, delta: -0.3632 },
  }
}

describe('ResultColumn', () => {
  it('renders the call metric card with title and hero number', () => {
    render(<ResultColumn side="call" inputs={ATM_INPUTS} result={priceResponse(10.4506, 5.5735)} />)
    expect(screen.getByText(/call value/i)).toBeInTheDocument()
    expect(screen.getByText('$10.4506')).toBeInTheDocument()
  })

  it('renders the put metric card with title and hero number', () => {
    render(<ResultColumn side="put" inputs={ATM_INPUTS} result={priceResponse(10.4506, 5.5735)} />)
    expect(screen.getByText(/put value/i)).toBeInTheDocument()
    expect(screen.getByText('$5.5735')).toBeInTheDocument()
  })

  it('marks the call ITM when S > K', () => {
    render(
      <ResultColumn side="call" inputs={ITM_CALL_INPUTS} result={priceResponse(17.66, 2.79)} />,
    )
    const card = document.querySelector('[data-component="MetricCard"]')
    expect(card?.querySelector('[data-element="tag"]')?.textContent).toMatch(/itm/i)
  })

  it('marks the put OTM when S > K', () => {
    render(<ResultColumn side="put" inputs={ITM_CALL_INPUTS} result={priceResponse(17.66, 2.79)} />)
    const card = document.querySelector('[data-component="MetricCard"]')
    expect(card?.querySelector('[data-element="tag"]')?.textContent).toMatch(/otm/i)
  })

  it('falls back to zero values when no result is available yet', () => {
    render(<ResultColumn side="call" inputs={ATM_INPUTS} result={null} />)
    expect(screen.getByText('$0.0000')).toBeInTheDocument()
  })

  it('renders the call greeks panel with the expected title', () => {
    render(<ResultColumn side="call" inputs={ATM_INPUTS} result={priceResponse(10.4506, 5.5735)} />)
    expect(screen.getByText(/call greeks/i)).toBeInTheDocument()
  })

  it('renders the put greeks panel with the expected title', () => {
    render(<ResultColumn side="put" inputs={ATM_INPUTS} result={priceResponse(10.4506, 5.5735)} />)
    expect(screen.getByText(/put greeks/i)).toBeInTheDocument()
  })
})
