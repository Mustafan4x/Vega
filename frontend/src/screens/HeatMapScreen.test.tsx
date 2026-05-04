import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

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

import { HeatMapScreen } from './HeatMapScreen'

const heatmapResponseBody = {
  call: [[1]],
  put: [[1]],
  model: 'black_scholes',
  sigma_axis: [0.2],
  spot_axis: [100],
}

const calculationCreateBody = {
  ...heatmapResponseBody,
  calculation_id: '00000000-0000-0000-0000-000000000001',
}

describe('HeatMapScreen Save button', () => {
  beforeEach(() => {
    resetAuth0MockState()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('triggers loginWithRedirect with pendingSave when logged out', async () => {
    const loginWithRedirect = vi.fn().mockResolvedValue(undefined)
    setAuth0MockState(makeAuth0Mock({ isAuthenticated: false, loginWithRedirect }))
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(heatmapResponseBody), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    render(<HeatMapScreen />)
    fireEvent.click(screen.getByRole('button', { name: /recompute/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /save/i })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    await waitFor(() => expect(loginWithRedirect).toHaveBeenCalledTimes(1))
    const arg = loginWithRedirect.mock.calls[0]?.[0] as
      | { appState?: { pendingSave?: unknown } }
      | undefined
    expect(arg?.appState?.pendingSave).toBeDefined()
  })

  it('saves directly when logged in', async () => {
    const getToken = vi.fn().mockResolvedValue('jwt-xyz')
    setAuth0MockState(makeAuth0Mock({ isAuthenticated: true, getAccessTokenSilently: getToken }))
    const fetchSpy = vi
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(heatmapResponseBody), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(calculationCreateBody), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
    render(<HeatMapScreen />)
    fireEvent.click(screen.getByRole('button', { name: /recompute/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /save/i })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    await waitFor(() => {
      const lastCall = fetchSpy.mock.calls.at(-1)
      const headers = (lastCall?.[1] as RequestInit | undefined)?.headers as
        | Record<string, string>
        | undefined
      expect(headers?.Authorization).toBe('Bearer jwt-xyz')
    })
  })
})
