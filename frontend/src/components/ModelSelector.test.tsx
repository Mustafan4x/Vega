import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ModelSelector } from './ModelSelector'

describe('ModelSelector', () => {
  it('renders three model tabs and a compare toggle', () => {
    render(
      <ModelSelector
        model="black_scholes"
        compare={false}
        onModelChange={() => {}}
        onCompareChange={() => {}}
      />,
    )

    expect(screen.getByRole('tab', { name: /black.?scholes/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /binomial/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /monte carlo/i })).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: /compare/i })).toBeInTheDocument()
  })

  it('marks the selected model tab with aria-selected', () => {
    render(
      <ModelSelector
        model="binomial"
        compare={false}
        onModelChange={() => {}}
        onCompareChange={() => {}}
      />,
    )

    expect(screen.getByRole('tab', { name: /binomial/i })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: /black.?scholes/i })).toHaveAttribute(
      'aria-selected',
      'false',
    )
  })

  it('calls onModelChange with the chosen model', async () => {
    const onModelChange = vi.fn()
    const user = userEvent.setup()
    render(
      <ModelSelector
        model="black_scholes"
        compare={false}
        onModelChange={onModelChange}
        onCompareChange={() => {}}
      />,
    )

    await user.click(screen.getByRole('tab', { name: /monte carlo/i }))

    expect(onModelChange).toHaveBeenCalledWith('monte_carlo')
  })

  it('calls onCompareChange when the toggle is clicked', async () => {
    const onCompareChange = vi.fn()
    const user = userEvent.setup()
    render(
      <ModelSelector
        model="black_scholes"
        compare={false}
        onModelChange={() => {}}
        onCompareChange={onCompareChange}
      />,
    )

    await user.click(screen.getByRole('switch', { name: /compare/i }))

    expect(onCompareChange).toHaveBeenCalledWith(true)
  })

  it('disables the model tabs while compare is on', () => {
    render(
      <ModelSelector
        model="black_scholes"
        compare={true}
        onModelChange={() => {}}
        onCompareChange={() => {}}
      />,
    )

    for (const name of [/black.?scholes/i, /binomial/i, /monte carlo/i]) {
      expect(screen.getByRole('tab', { name })).toBeDisabled()
    }
  })
})
