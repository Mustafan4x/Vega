import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

import { ResultPanel } from './ResultPanel'

const ATM_INPUTS = { S: 100, K: 100, T: 1, r: 0.05, sigma: 0.2 }
const ITM_CALL_INPUTS = { S: 110, K: 100, T: 1, r: 0.05, sigma: 0.2 }

describe('ResultPanel', () => {
  it('renders both metric cards with title and hero number when result is provided', () => {
    render(<ResultPanel inputs={ATM_INPUTS} result={{ call: 10.4506, put: 5.5735 }} />)

    expect(screen.getByText(/call value/i)).toBeInTheDocument()
    expect(screen.getByText(/put value/i)).toBeInTheDocument()
    expect(screen.getByText('$10.4506')).toBeInTheDocument()
    expect(screen.getByText('$5.5735')).toBeInTheDocument()
  })

  it('marks the call ITM and the put OTM when S > K', () => {
    render(<ResultPanel inputs={ITM_CALL_INPUTS} result={{ call: 17.66, put: 2.79 }} />)

    const cards = document.querySelectorAll('[data-component="MetricCard"]')
    const callCard = cards[0]
    const putCard = cards[1]
    expect(callCard.querySelector('[data-element="tag"]')?.textContent).toMatch(/itm/i)
    expect(putCard.querySelector('[data-element="tag"]')?.textContent).toMatch(/otm/i)
  })

  it('falls back to zero values when no result is available yet', () => {
    render(<ResultPanel inputs={ATM_INPUTS} result={null} />)

    expect(screen.getAllByText('$0.0000').length).toBe(2)
  })
})
