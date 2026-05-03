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

  it('renders a placeholder when a not yet shipped nav item is active', async () => {
    const user = (await import('@testing-library/user-event')).default.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /history/i }))

    expect(screen.getByText(/coming in phase 6/i)).toBeInTheDocument()
  })
})
