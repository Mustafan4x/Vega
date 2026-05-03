import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { TickerAutocomplete } from './TickerAutocomplete'
import * as api from '../lib/api'

function quoteResponse(): Response {
  return new Response(
    JSON.stringify({ symbol: 'AAPL', name: 'Apple Inc.', price: 199.5, currency: 'USD' }),
    { status: 200, headers: { 'Content-Type': 'application/json' } },
  )
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('TickerAutocomplete', () => {
  const fetchSpy = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchSpy.mockReset()
    vi.stubGlobal('fetch', fetchSpy)
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('renders the search input with an accessible label', () => {
    render(<TickerAutocomplete onApply={() => {}} />)

    expect(screen.getByRole('searchbox', { name: /ticker symbol/i })).toBeInTheDocument()
  })

  it('debounces input and looks up after 250ms of inactivity', async () => {
    fetchSpy.mockResolvedValue(quoteResponse())
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<TickerAutocomplete onApply={() => {}} />)

    await user.type(screen.getByRole('searchbox'), 'AAPL')
    expect(fetchSpy).not.toHaveBeenCalled()

    await act(async () => {
      vi.advanceTimersByTime(260)
    })

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url] = fetchSpy.mock.calls[0]
    expect(String(url)).toMatch(/\/api\/tickers\/AAPL$/)
  })

  it('only fires once for a burst of keystrokes', async () => {
    fetchSpy.mockResolvedValue(quoteResponse())
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<TickerAutocomplete onApply={() => {}} />)

    await user.type(screen.getByRole('searchbox'), 'A')
    await user.type(screen.getByRole('searchbox'), 'A')
    await user.type(screen.getByRole('searchbox'), 'P')
    await user.type(screen.getByRole('searchbox'), 'L')

    await act(async () => {
      vi.advanceTimersByTime(260)
    })

    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })

  it('renders the resolved quote and an Apply button on success', async () => {
    fetchSpy.mockResolvedValue(quoteResponse())
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<TickerAutocomplete onApply={() => {}} />)

    await user.type(screen.getByRole('searchbox'), 'AAPL')
    await act(async () => {
      vi.advanceTimersByTime(260)
    })
    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(screen.getByText(/Apple Inc\./)).toBeInTheDocument()
    expect(screen.getByText(/199\.50/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /use price/i })).toBeEnabled()
  })

  it('calls onApply with the resolved price when the button is clicked', async () => {
    fetchSpy.mockResolvedValue(quoteResponse())
    const onApply = vi.fn()
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<TickerAutocomplete onApply={onApply} />)

    await user.type(screen.getByRole('searchbox'), 'AAPL')
    await act(async () => {
      vi.advanceTimersByTime(260)
    })
    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })
    await user.click(screen.getByRole('button', { name: /use price/i }))

    expect(onApply).toHaveBeenCalledWith({
      symbol: 'AAPL',
      name: 'Apple Inc.',
      price: 199.5,
      currency: 'USD',
    })
  })

  it('shows "Symbol not found" on a 404', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(404, { detail: 'Ticker not found.' }))
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<TickerAutocomplete onApply={() => {}} />)

    await user.type(screen.getByRole('searchbox'), 'ZZZZ')
    await act(async () => {
      vi.advanceTimersByTime(260)
    })
    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(screen.getByRole('alert')).toHaveTextContent(/no data for that symbol/i)
    expect(screen.queryByRole('button', { name: /use price/i })).not.toBeInTheDocument()
  })

  it('does not fire the lookup for client-invalid symbols', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<TickerAutocomplete onApply={() => {}} />)

    await user.type(screen.getByRole('searchbox'), '!!!')
    await act(async () => {
      vi.advanceTimersByTime(400)
    })

    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('uppercases user input before showing it back', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<TickerAutocomplete onApply={() => {}} />)

    const input = screen.getByRole('searchbox') as HTMLInputElement
    await user.type(input, 'aapl')

    expect(input.value).toBe('AAPL')
  })

  it('clears the result when the input is emptied', async () => {
    fetchSpy.mockResolvedValue(quoteResponse())
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<TickerAutocomplete onApply={() => {}} />)

    const input = screen.getByRole('searchbox')
    await user.type(input, 'AAPL')
    await act(async () => {
      vi.advanceTimersByTime(260)
    })
    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(screen.getByText(/Apple Inc\./)).toBeInTheDocument()

    await user.clear(input)
    await act(async () => {
      vi.advanceTimersByTime(260)
    })

    expect(screen.queryByText(/Apple Inc\./)).not.toBeInTheDocument()
  })
})

// Also import api so the mocked fetch reaches the real fetchTicker.
void api
