import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { InputForm } from './InputForm'
import type { PriceRequest } from '../lib/api'

const INPUTS: PriceRequest = { S: 100, K: 100, T: 1, r: 0.05, sigma: 0.2 }

describe('InputForm', () => {
  it('renders all five Black Scholes inputs and the Calculate button', () => {
    render(
      <InputForm
        inputs={INPUTS}
        invalid={new Set()}
        pending={false}
        onChange={() => {}}
        onCalculate={() => {}}
      />,
    )

    expect(screen.getByLabelText(/asset price \(s\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/strike \(k\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/time to expiry \(t\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/risk free rate \(r\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/volatility \(sigma\)/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /calculate/i })).toBeEnabled()
  })

  it('renders r and sigma in percent', () => {
    render(
      <InputForm
        inputs={INPUTS}
        invalid={new Set()}
        pending={false}
        onChange={() => {}}
        onCalculate={() => {}}
      />,
    )

    expect(screen.getByLabelText(/risk free rate \(r\)/i)).toHaveValue('5')
    expect(screen.getByLabelText(/volatility \(sigma\)/i)).toHaveValue('20')
  })

  it('disables Calculate while a request is pending', () => {
    render(
      <InputForm
        inputs={INPUTS}
        invalid={new Set()}
        pending={true}
        onChange={() => {}}
        onCalculate={() => {}}
      />,
    )

    const btn = screen.getByRole('button', { name: /calculating/i })
    expect(btn).toBeDisabled()
    expect(btn).toHaveAttribute('aria-busy', 'true')
  })

  it('marks the field invalid when reported by the parent', () => {
    render(
      <InputForm
        inputs={INPUTS}
        invalid={new Set(['S'])}
        pending={false}
        onChange={() => {}}
        onCalculate={() => {}}
      />,
    )

    expect(screen.getByLabelText(/asset price \(s\)/i)).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText(/strike \(k\)/i)).toHaveAttribute('aria-invalid', 'false')
  })

  it('calls onCalculate when the form is submitted', async () => {
    const user = userEvent.setup()
    const onCalculate = vi.fn()
    render(
      <InputForm
        inputs={INPUTS}
        invalid={new Set()}
        pending={false}
        onChange={() => {}}
        onCalculate={onCalculate}
      />,
    )

    await user.click(screen.getByRole('button', { name: /calculate/i }))

    expect(onCalculate).toHaveBeenCalledTimes(1)
  })
})
