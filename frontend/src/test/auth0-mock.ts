import { vi } from 'vitest'

export interface MockAuth0State {
  isAuthenticated: boolean
  isLoading: boolean
  user?: { sub: string; email?: string; name?: string }
  getAccessTokenSilently: ReturnType<typeof vi.fn>
  loginWithRedirect: ReturnType<typeof vi.fn>
  logout: ReturnType<typeof vi.fn>
  handleRedirectCallback: ReturnType<typeof vi.fn>
}

export function makeAuth0Mock(overrides: Partial<MockAuth0State> = {}): MockAuth0State {
  return {
    isAuthenticated: false,
    isLoading: false,
    user: undefined,
    getAccessTokenSilently: vi.fn().mockResolvedValue('test.jwt.token'),
    loginWithRedirect: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    handleRedirectCallback: vi.fn().mockResolvedValue({ appState: {} }),
    ...overrides,
  }
}

let currentState: MockAuth0State = makeAuth0Mock()

export function setAuth0MockState(state: MockAuth0State): void {
  currentState = state
}

export function getAuth0MockState(): MockAuth0State {
  return currentState
}

export function resetAuth0MockState(): void {
  currentState = makeAuth0Mock()
}
