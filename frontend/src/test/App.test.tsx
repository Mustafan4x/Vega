import { render, screen } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders the layout shell with primary navigation and the pricing screen', () => {
    render(<App />)

    expect(screen.getByRole('navigation', { name: /primary navigation/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /inputs/i })).toBeInTheDocument()
    expect(document.querySelector('[data-component="PricingScreen"]')).not.toBeNull()
  })

  it('renders the HeatMap screen when the heatmap nav item is active', async () => {
    const user = (await import('@testing-library/user-event')).default.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /heat map/i }))

    expect(document.querySelector('[data-component="HeatMapScreen"]')).not.toBeNull()
    expect(screen.getByRole('button', { name: /recompute heat map/i })).toBeInTheDocument()
  })

  it('renders the Backtest screen when the backtest nav item is active', async () => {
    const user = (await import('@testing-library/user-event')).default.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /backtest/i }))

    expect(document.querySelector('[data-component="BacktestScreen"]')).not.toBeNull()
    expect(screen.getByRole('button', { name: /run backtest/i })).toBeInTheDocument()
  })

  it('exposes only the implemented screens in the sidebar nav', () => {
    render(<App />)

    const nav = screen.getByRole('navigation', { name: /primary navigation/i })
    expect(nav).toBeInTheDocument()
    // Pricing, Heat Map, Backtest are wired end to end. The dead
    // "Model Comparison" and "History" nav items were removed in the
    // Phase 11 closeout (Compare is a toggle on Pricing; History is
    // tracked in docs/future-ideas.md).
    expect(screen.getByRole('button', { name: /pricing/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /heat map/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /backtest/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /model comparison/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /history/i })).toBeNull()
  })
})
