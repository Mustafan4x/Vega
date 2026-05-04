import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  getAuth0MockState,
  makeAuth0Mock,
  resetAuth0MockState,
  setAuth0MockState,
} from '../test/auth0-mock'

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => getAuth0MockState(),
  Auth0Provider: ({ children }: { children: unknown }) => children,
}))

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { LayoutShell } from './LayoutShell'

describe('LayoutShell', () => {
  it('marks the active nav item with data-active and aria-current', () => {
    render(
      <LayoutShell active="pricing" onNav={() => {}}>
        <div>content</div>
      </LayoutShell>,
    )

    const pricing = screen.getByRole('button', { name: /pricing/i })
    expect(pricing).toHaveAttribute('data-active', 'true')
    expect(pricing).toHaveAttribute('aria-current', 'page')
    const heatmap = screen.getByRole('button', { name: /heat map/i })
    expect(heatmap).toHaveAttribute('data-active', 'false')
  })

  it('calls onNav with the clicked screen id', async () => {
    const user = userEvent.setup()
    const onNav = vi.fn()
    render(
      <LayoutShell active="pricing" onNav={onNav}>
        <div>content</div>
      </LayoutShell>,
    )

    await user.click(screen.getByRole('button', { name: /backtest/i }))

    expect(onNav).toHaveBeenCalledWith('backtest')
  })

  it('renders children and shows the active screen label in breadcrumbs', () => {
    render(
      <LayoutShell active="backtest" onNav={() => {}}>
        <div data-testid="content">hello</div>
      </LayoutShell>,
    )

    expect(screen.getByTestId('content')).toBeInTheDocument()
    const crumb = document.querySelector('[data-component="TopBar"] [data-element="crumb"]')
    expect(crumb?.textContent).toMatch(/backtest/i)
  })
})

describe('LayoutShell auth surface', () => {
  beforeEach(() => {
    resetAuth0MockState()
  })

  it('shows the sign-in button when logged out', () => {
    setAuth0MockState(makeAuth0Mock({ isAuthenticated: false }))
    render(
      <LayoutShell active="pricing" onNav={() => {}}>
        <div />
      </LayoutShell>,
    )
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows the user button when logged in', () => {
    setAuth0MockState(
      makeAuth0Mock({
        isAuthenticated: true,
        user: { sub: 'google-oauth2|123', email: 'me@example.com' },
      }),
    )
    render(
      <LayoutShell active="pricing" onNav={() => {}}>
        <div />
      </LayoutShell>,
    )
    expect(screen.getByText('me@example.com')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()
  })
})
