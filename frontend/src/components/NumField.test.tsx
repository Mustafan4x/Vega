import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { NumField } from './NumField'

describe('NumField', () => {
  it('shows the label, suffix, and value', () => {
    render(<NumField label="Asset Price (S)" suffix="USD" value={100} onChange={() => {}} />)

    expect(screen.getByLabelText(/asset price/i)).toHaveValue('100')
    expect(screen.getByText('USD')).toBeInTheDocument()
  })

  it('emits onChange with parsed value while typing valid decimals', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<NumField label="Strike" value={0} onChange={onChange} />)

    const input = screen.getByLabelText(/strike/i)
    await user.clear(input)
    await user.type(input, '42.5')

    expect(onChange).toHaveBeenLastCalledWith(42.5)
  })

  it('clamps to min on blur when the draft is unparseable', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<NumField label="Time" value={1} min={0} onChange={onChange} />)

    const input = screen.getByLabelText(/time/i)
    await user.clear(input)
    await user.tab()

    expect(onChange).toHaveBeenLastCalledWith(0)
  })

  it('marks the input invalid when invalid is true', () => {
    render(<NumField label="Vol" value={0.2} invalid={true} onChange={() => {}} />)

    expect(screen.getByLabelText(/vol/i)).toHaveAttribute('aria-invalid', 'true')
  })
})
