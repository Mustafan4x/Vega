import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { HeatMapControls, type HeatMapControlsState } from './HeatMapControls'

const BASE: HeatMapControlsState = {
  mode: 'value',
  volShock: [-0.5, 0.5],
  spotShock: [-0.3, 0.3],
  resolution: 9,
  callBasis: 10,
  putBasis: 5,
}

describe('HeatMapControls', () => {
  it('switches mode when the user clicks a tab', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <HeatMapControls inputs={BASE} pending={false} onChange={onChange} onRecompute={() => {}} />,
    )

    await user.click(screen.getByRole('tab', { name: /p&l/i }))

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ mode: 'pl' }))
  })

  it('shows the basis fields only in pl mode', () => {
    const { rerender } = render(
      <HeatMapControls inputs={BASE} pending={false} onChange={() => {}} onRecompute={() => {}} />,
    )
    expect(screen.queryByLabelText(/call paid/i)).toBeNull()

    rerender(
      <HeatMapControls
        inputs={{ ...BASE, mode: 'pl' }}
        pending={false}
        onChange={() => {}}
        onRecompute={() => {}}
      />,
    )

    expect(screen.getByLabelText(/call paid/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/put paid/i)).toBeInTheDocument()
  })

  it('disables the recompute button while pending', () => {
    render(
      <HeatMapControls inputs={BASE} pending={true} onChange={() => {}} onRecompute={() => {}} />,
    )

    const btn = screen.getByRole('button', { name: /computing/i })
    expect(btn).toBeDisabled()
    expect(btn).toHaveAttribute('aria-busy', 'true')
  })

  it('calls onRecompute when the button is clicked', async () => {
    const user = userEvent.setup()
    const onRecompute = vi.fn()
    render(
      <HeatMapControls
        inputs={BASE}
        pending={false}
        onChange={() => {}}
        onRecompute={onRecompute}
      />,
    )

    await user.click(screen.getByRole('button', { name: /recompute heat map/i }))

    expect(onRecompute).toHaveBeenCalledTimes(1)
  })

  it('changes the resolution via the select', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <HeatMapControls inputs={BASE} pending={false} onChange={onChange} onRecompute={() => {}} />,
    )

    await user.selectOptions(screen.getByLabelText(/resolution/i), '13')

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ resolution: 13 }))
  })
})
