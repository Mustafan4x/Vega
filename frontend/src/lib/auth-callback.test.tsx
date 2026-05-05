import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'

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

import { AuthCallback } from './auth-callback'

describe('AuthCallback', () => {
  beforeEach(() => {
    resetAuth0MockState()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('replays pendingSave once and redirects home', async () => {
    const handleRedirectCallback = vi.fn().mockResolvedValue({
      appState: {
        pendingSave: {
          request: {
            S: 100,
            K: 100,
            T: 1,
            r: 0.05,
            sigma: 0.2,
            vol_shock: [-0.5, 0.5],
            spot_shock: [-0.3, 0.3],
            rows: 5,
            cols: 5,
          },
        },
      },
    })
    const getToken = vi.fn().mockResolvedValue('jwt-cb')
    setAuth0MockState(
      makeAuth0Mock({
        isAuthenticated: true,
        handleRedirectCallback,
        getAccessTokenSilently: getToken,
      }),
    )
    const calculationCreateBody = {
      calculation_id: '00000000-0000-0000-0000-000000000001',
      call: [[1]],
      put: [[1]],
      model: 'black_scholes',
      sigma_axis: [0.2],
      spot_axis: [100],
    }
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(calculationCreateBody), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    const replaceSpy = vi.spyOn(window.history, 'replaceState')

    render(<AuthCallback />)

    await waitFor(() => expect(handleRedirectCallback).toHaveBeenCalled())
    await waitFor(() => expect(fetchSpy).toHaveBeenCalled())
    await waitFor(() => expect(replaceSpy).toHaveBeenCalledWith({}, '', '/'))
  })

  it('dispatches a popstate event after successful redirect so the App leaves /callback', async () => {
    const handleRedirectCallback = vi.fn().mockResolvedValue({ appState: undefined })
    setAuth0MockState(makeAuth0Mock({ isAuthenticated: true, handleRedirectCallback }))

    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

    render(<AuthCallback />)

    await waitFor(() => expect(handleRedirectCallback).toHaveBeenCalled())
    await waitFor(() => {
      const popstateCalls = dispatchSpy.mock.calls.filter(
        ([event]) => event instanceof PopStateEvent && event.type === 'popstate',
      )
      expect(popstateCalls.length).toBeGreaterThan(0)
    })
  })
})
