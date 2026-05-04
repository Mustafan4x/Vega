import { describe, it, expect, vi } from 'vitest'
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
