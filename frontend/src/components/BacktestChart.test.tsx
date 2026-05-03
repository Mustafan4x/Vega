import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { BacktestChart } from './BacktestChart'
import type { BacktestResponse } from '../lib/api'

function makeResult(pnl: number[]): BacktestResponse {
  const n = pnl.length
  return {
    symbol: 'AAPL',
    strategy: 'long_call',
    dates: Array.from({ length: n }, (_, i) => `2026-01-${String(2 + i).padStart(2, '0')}`),
    spot: Array(n).fill(100),
    position_value: pnl.map((p) => 3 + p),
    pnl,
    strike: 100,
    entry_basis: 3,
    entry_date: '2026-01-02',
    expiry_date: '2026-02-01',
    legs: [{ sign: 1, kind: 'call' }],
  }
}

describe('BacktestChart', () => {
  it('renders an empty placeholder when result is null', () => {
    render(<BacktestChart result={null} />)
    expect(screen.getByText(/run a backtest/i)).toBeInTheDocument()
  })

  it('renders the SVG with a polyline of P&L points when result is provided', () => {
    const { container } = render(<BacktestChart result={makeResult([0, 1.0, -0.5, 2.0])} />)

    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    const polyline = container.querySelector('polyline[data-element="pnlLine"]')
    expect(polyline).toBeInTheDocument()
    const points = polyline?.getAttribute('points') ?? ''
    expect(points.split(' ')).toHaveLength(4)
  })

  it('shows the final P&L in the card meta', () => {
    render(<BacktestChart result={makeResult([0, 1, 2, 3.5])} />)
    expect(screen.getByText(/final \$3\.50/i)).toBeInTheDocument()
  })

  it('shows a negative final P&L with a leading dash', () => {
    render(<BacktestChart result={makeResult([0, -1, -2, -1.25])} />)
    expect(screen.getByText(/-\$1\.25/)).toBeInTheDocument()
  })

  it('uses the accent color when the curve ends positive and primary when negative', () => {
    const { container, rerender } = render(<BacktestChart result={makeResult([0, 1, 2, 5])} />)
    let polyline = container.querySelector('polyline[data-element="pnlLine"]')
    expect(polyline?.getAttribute('stroke')).toContain('accent')

    rerender(<BacktestChart result={makeResult([0, -1, -3, -5])} />)
    polyline = container.querySelector('polyline[data-element="pnlLine"]')
    expect(polyline?.getAttribute('stroke')).toContain('primary')
  })
})
