import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { GreeksPanel } from './GreeksPanel'
import type { GreeksDisplay } from '../lib/api'

const SAMPLE: GreeksDisplay = {
  delta: 0.6368,
  gamma: 0.01876,
  theta_per_day: -0.01757,
  vega_per_pct: 0.3752,
  rho_per_pct: 0.5323,
}

describe('GreeksPanel', () => {
  it('renders all five tiles with the glyphs and labels', () => {
    render(<GreeksPanel title="Call Greeks" greeks={SAMPLE} />)

    const cells = document.querySelectorAll('[data-element="tile"]')
    expect(cells.length).toBe(5)

    expect(screen.getByText('Delta')).toBeInTheDocument()
    expect(screen.getByText('Gamma')).toBeInTheDocument()
    expect(screen.getByText('Theta')).toBeInTheDocument()
    expect(screen.getByText('Vega')).toBeInTheDocument()
    expect(screen.getByText('Rho')).toBeInTheDocument()
  })

  it('formats the values in their display units', () => {
    render(<GreeksPanel title="Call Greeks" greeks={SAMPLE} />)

    expect(screen.getByText('0.6368')).toBeInTheDocument()
    expect(screen.getByText('0.01876')).toBeInTheDocument()
    expect(screen.getByText('-$0.0176')).toBeInTheDocument()
    expect(screen.getByText('$0.3752')).toBeInTheDocument()
    expect(screen.getByText('$0.5323')).toBeInTheDocument()
  })

  it('cycles the data-accent across the five tiles', () => {
    render(<GreeksPanel title="Call Greeks" greeks={SAMPLE} />)

    const accents = Array.from(document.querySelectorAll('[data-element="tile"]')).map((el) =>
      el.getAttribute('data-accent'),
    )
    expect(accents).toEqual(['primary', 'accent', 'amber', 'info', 'violet'])
  })

  it('exposes accessible labels with units for theta, vega, rho', () => {
    render(<GreeksPanel title="Call Greeks" greeks={SAMPLE} />)

    const groups = Array.from(document.querySelectorAll('[data-element="tile"]'))
    const labels = groups.map((g) => g.getAttribute('aria-label'))
    expect(labels[2]).toMatch(/Theta -\$0\.0176 per day/)
    expect(labels[3]).toMatch(/Vega \$0\.3752 per 1 percent of sigma/)
    expect(labels[4]).toMatch(/Rho \$0\.5323 per 1 percent of r/)
  })

  it('shows em dashes for tile values when no greeks are supplied yet', () => {
    render(<GreeksPanel title="Call Greeks" greeks={null} />)

    const dashes = document.querySelectorAll('[data-element="value"]')
    expect(dashes.length).toBe(5)
    for (const el of dashes) {
      expect(el.textContent).toBe('—')
    }
  })
})
