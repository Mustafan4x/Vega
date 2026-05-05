import { useAuth0 } from '@auth0/auth0-react'
import type { JSX } from 'react'

export function SignInButton(): JSX.Element {
  const { loginWithRedirect, isLoading } = useAuth0()
  return (
    <button
      type="button"
      className="tr-btn tr-btn--primary"
      data-element="signInButton"
      onClick={() => void loginWithRedirect()}
      disabled={isLoading}
    >
      Sign in
    </button>
  )
}

export function UserButton(): JSX.Element | null {
  const { user, logout, isAuthenticated } = useAuth0()
  if (!isAuthenticated || !user) return null
  return (
    <div data-element="userButton">
      <span aria-label="Signed in as">{user.email ?? user.name ?? user.sub}</span>
      <button
        type="button"
        className="tr-btn tr-btn--primary"
        data-element="signOutButton"
        onClick={() => void logout({ logoutParams: { returnTo: window.location.origin } })}
      >
        Sign out
      </button>
    </div>
  )
}
