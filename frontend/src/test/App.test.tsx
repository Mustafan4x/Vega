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

  it('exposes all four screens in the sidebar nav', () => {
    render(<App />)

    const nav = screen.getByRole('navigation', { name: /primary navigation/i })
    expect(nav).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /pricing/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /heat map/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /backtest/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /history/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /model comparison/i })).toBeNull()
  })

  it('renders the History screen when History is active', async () => {
    const user = (await import('@testing-library/user-event')).default.setup()
    // History on mount calls fetchCalculations; stub it.
    const fetchSpy = (await import('vitest')).vi.fn<typeof fetch>()
    fetchSpy.mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, limit: 20, offset: 0 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    const { vi } = await import('vitest')
    vi.stubGlobal('fetch', fetchSpy)

    try {
      render(<App />)

      await user.click(screen.getByRole('button', { name: /history/i }))

      expect(document.querySelector('[data-component="HistoryScreen"]')).not.toBeNull()
    } finally {
      vi.unstubAllGlobals()
    }
  })
})
