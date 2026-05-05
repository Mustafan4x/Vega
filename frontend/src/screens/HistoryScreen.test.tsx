import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
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

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { HistoryScreen } from './HistoryScreen'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const SAMPLE_LIST = {
  items: [
    {
      calculation_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      created_at: '2026-05-04T03:32:21.000Z',
      s: 100,
      k: 100,
      t: 1,
      r: 0.05,
      sigma: 0.2,
      q: 0.025,
      rows: 5,
      cols: 5,
    },
    {
      calculation_id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
      created_at: '2026-05-04T03:30:00.000Z',
      s: 250,
      k: 240,
      t: 0.5,
      r: 0.04,
      sigma: 0.35,
      q: 0,
      rows: 9,
      cols: 9,
    },
  ],
  total: 2,
  limit: 20,
  offset: 0,
}

describe('HistoryScreen', () => {
  const fetchSpy = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchSpy.mockReset()
    vi.stubGlobal('fetch', fetchSpy)
    setAuth0MockState(
      makeAuth0Mock({
        isAuthenticated: true,
        user: { sub: 'test|user' },
      }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    resetAuth0MockState()
  })

  it('renders the empty state when no calculations exist', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(200, { items: [], total: 0, limit: 20, offset: 0 }))

    render(<HistoryScreen />)

    expect(await screen.findByText(/no saved calculations yet/i)).toBeInTheDocument()
  })

  it('renders rows for each calculation in the list', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(200, SAMPLE_LIST))

    render(<HistoryScreen />)

    expect(await screen.findByText(/2 total/i)).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /load/i })).toHaveLength(2)
    // Spot check the second row's K and grid size.
    expect(screen.getByText('240.00')).toBeInTheDocument()
    expect(screen.getByText('9 x 9')).toBeInTheDocument()
  })

  it('loads the detail when a row is clicked', async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(200, SAMPLE_LIST)).mockResolvedValueOnce(
      jsonResponse(200, {
        calculation_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        s: 100,
        k: 100,
        t: 1,
        r: 0.05,
        sigma: 0.2,
        q: 0.025,
        rows: 2,
        cols: 2,
        call: [
          [10, 11],
          [12, 13],
        ],
        put: [
          [5, 6],
          [7, 8],
        ],
        sigma_axis: [0.18, 0.22],
        spot_axis: [95, 105],
      }),
    )

    const user = userEvent.setup()
    render(<HistoryScreen />)

    const loadButtons = await screen.findAllByRole('button', { name: /load/i })
    await user.click(loadButtons[0])

    await waitFor(() => {
      // Two HeatMap components render in the detail card.
      expect(document.querySelectorAll('[data-component="HeatMap"]')).toHaveLength(1)
      expect(document.querySelectorAll('[data-component="PnlHeatMap"]')).toHaveLength(1)
    })

    const detailInputs = document.querySelector('[data-element="detailInputs"]')
    expect(detailInputs).not.toBeNull()
    expect(detailInputs?.querySelector('[data-pair="q"] dd')?.textContent).toBe('2.5%')
  })

  it('renders q as a percent in the summary table for each row', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(200, SAMPLE_LIST))

    render(<HistoryScreen />)

    await screen.findByText(/2 total/i)
    const qCells = document.querySelectorAll('td[data-element="q"]')
    expect(qCells.length).toBe(2)
    expect(qCells[0].textContent).toBe('2.5%')
    expect(qCells[1].textContent).toBe('0.0%')
  })

  it('shows an error message when the list fetch fails', async () => {
    fetchSpy.mockResolvedValue(jsonResponse(500, { detail: 'boom' }))

    render(<HistoryScreen />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})

describe('HistoryScreen auth gating', () => {
  beforeEach(() => {
    resetAuth0MockState()
  })

  it('renders the empty state when logged out', async () => {
    setAuth0MockState(makeAuth0Mock({ isAuthenticated: false }))
    render(<HistoryScreen />)
    expect(await screen.findByText(/sign in to see your saved calculations/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('fetches with a bearer token when logged in', async () => {
    const getToken = vi.fn().mockResolvedValue('jwt-abc')
    setAuth0MockState(
      makeAuth0Mock({
        isAuthenticated: true,
        getAccessTokenSilently: getToken,
        user: { sub: 'github|user-x' },
      }),
    )
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, limit: 20, offset: 0 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    render(<HistoryScreen />)
    await screen.findByText(/saved calculations/i)
    const call = fetchSpy.mock.calls[0]
    const opts = call?.[1] as RequestInit | undefined
    const headers = (opts?.headers ?? {}) as Record<string, string>
    expect(headers.Authorization).toBe('Bearer jwt-abc')
    fetchSpy.mockRestore()
  })
})
