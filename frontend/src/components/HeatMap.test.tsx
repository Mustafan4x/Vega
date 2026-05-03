import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { HeatMap } from './HeatMap'

const SMALL_GRID = [
  [1, 2, 3],
  [4, 5, 6],
  [7, 8, 9],
]
const SIGMA = [0.1, 0.2, 0.3]
const SPOT = [80, 100, 120]

describe('HeatMap', () => {
  it('renders the data-component selector and the title', () => {
    render(
      <HeatMap
        dataComp="HeatMap"
        title="Call value"
        grid={SMALL_GRID}
        vAxis={SIGMA}
        sAxis={SPOT}
        mode="value"
        basis={0}
      />,
    )

    expect(document.querySelector('[data-component="HeatMap"]')).not.toBeNull()
    expect(screen.getByRole('heading', { name: /call value/i })).toBeInTheDocument()
  })

  it('renders the right number of hit grid cells', () => {
    render(
      <HeatMap
        dataComp="HeatMap"
        title="Call value"
        grid={SMALL_GRID}
        vAxis={SIGMA}
        sAxis={SPOT}
        mode="value"
        basis={0}
      />,
    )

    const cells = document.querySelectorAll('[data-element="cell"]')
    expect(cells.length).toBe(SMALL_GRID.length * SMALL_GRID[0].length)
  })

  it('gives every cell an aria-label that names sigma, spot, and value', () => {
    render(
      <HeatMap
        dataComp="HeatMap"
        title="Call value"
        grid={SMALL_GRID}
        vAxis={SIGMA}
        sAxis={SPOT}
        mode="value"
        basis={0}
      />,
    )

    const cells = document.querySelectorAll('[data-element="cell"]')
    for (const cell of cells) {
      const label = cell.getAttribute('aria-label') ?? ''
      expect(label).toMatch(/Sigma/)
      expect(label).toMatch(/spot/)
      expect(label).toMatch(/value/)
    }
  })

  it('uses P&L wording in pl mode', () => {
    render(
      <HeatMap
        dataComp="PnlHeatMap"
        title="Call P&L"
        grid={SMALL_GRID}
        vAxis={SIGMA}
        sAxis={SPOT}
        mode="pl"
        basis={5}
      />,
    )

    const firstCell = document.querySelector('[data-element="cell"]')
    expect(firstCell?.getAttribute('aria-label')).toMatch(/P&L/)
  })

  it('renders empty cells when grid is empty', () => {
    render(
      <HeatMap
        dataComp="HeatMap"
        title="Call value"
        grid={[]}
        vAxis={[]}
        sAxis={[]}
        mode="value"
        basis={0}
      />,
    )

    expect(document.querySelectorAll('[data-element="cell"]').length).toBe(0)
  })

  it('exposes the canvas with an accessible label', () => {
    render(
      <HeatMap
        dataComp="HeatMap"
        title="Call value"
        grid={SMALL_GRID}
        vAxis={SIGMA}
        sAxis={SPOT}
        mode="value"
        basis={0}
      />,
    )

    const canvas = document.querySelector('[data-element="canvas"]')
    expect(canvas).not.toBeNull()
    expect(canvas?.getAttribute('aria-label')).toMatch(/heat map/i)
  })
})
