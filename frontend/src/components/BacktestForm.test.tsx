import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { BacktestForm } from './BacktestForm'
import type { BacktestRequest } from '../lib/api'

const INPUTS: BacktestRequest = {
  symbol: 'AAPL',
  strategy: 'long_call',
  start_date: '2026-01-02',
  end_date: '2026-02-15',
  sigma: 0.2,
  r: 0.05,
  dte_days: 30,
}

describe('BacktestForm', () => {
  it('renders the symbol, strategy, dates, dte, sigma, r inputs and a Run button', () => {
    render(
      <BacktestForm
        inputs={INPUTS}
        invalid={new Set()}
        pending={false}
        onChange={() => {}}
        onRun={() => {}}
      />,
    )

    expect(screen.getByLabelText(/ticker symbol/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/strategy/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/start date/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/end date/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/days to expiry/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/implied volatility/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/risk free rate/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /run backtest/i })).toBeEnabled()
  })

  it('uppercases the symbol on input', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <BacktestForm
        inputs={INPUTS}
        invalid={new Set()}
        pending={false}
        onChange={onChange}
        onRun={() => {}}
      />,
    )

    const input = screen.getByLabelText(/ticker symbol/i)
    await user.clear(input)
    await user.type(input, 'msft')

    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0]
    expect(lastCall.symbol).toMatch(/^[A-Z]+$/)
  })

  it('disables Run while pending', () => {
    render(
      <BacktestForm
        inputs={INPUTS}
        invalid={new Set()}
        pending={true}
        onChange={() => {}}
        onRun={() => {}}
      />,
    )
    const btn = screen.getByRole('button', { name: /running/i })
    expect(btn).toBeDisabled()
    expect(btn).toHaveAttribute('aria-busy', 'true')
  })

  it('calls onRun when the form is submitted', async () => {
    const onRun = vi.fn()
    const user = userEvent.setup()
    render(
      <BacktestForm
        inputs={INPUTS}
        invalid={new Set()}
        pending={false}
        onChange={() => {}}
        onRun={onRun}
      />,
    )

    await user.click(screen.getByRole('button', { name: /run backtest/i }))

    expect(onRun).toHaveBeenCalledTimes(1)
  })

  it('marks invalid fields with aria-invalid', () => {
    render(
      <BacktestForm
        inputs={INPUTS}
        invalid={new Set(['symbol', 'dte_days'])}
        pending={false}
        onChange={() => {}}
        onRun={() => {}}
      />,
    )
    expect(screen.getByLabelText(/ticker symbol/i)).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText(/days to expiry/i)).toHaveAttribute('aria-invalid', 'true')
  })
})
