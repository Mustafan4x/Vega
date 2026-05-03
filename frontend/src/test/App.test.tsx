import { render, screen } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders the layout shell with primary navigation and the pricing screen', () => {
    render(<App />)

    expect(screen.getByRole('navigation', { name: /primary navigation/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /inputs/i })).toBeInTheDocument()
    expect(document.querySelector('[data-component="PricingScreen"]')).not.toBeNull()
  })

  it('renders a placeholder when a non pricing nav item is active', async () => {
    const user = (await import('@testing-library/user-event')).default.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /heat map/i }))

    expect(screen.getByRole('heading', { name: /heat map/i })).toBeInTheDocument()
    expect(screen.getByText(/coming in phase 4/i)).toBeInTheDocument()
  })
})
