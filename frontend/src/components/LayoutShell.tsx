/**
 * Application shell: sidebar nav, sticky top bar, and a content slot.
 * Component anatomy mirrors the canonical reference at
 * ``docs/design/claude-design-output.html`` so designers can map between
 * the two by selector.
 */

import type { ReactNode } from 'react'
import { useAuth0 } from '@auth0/auth0-react'

import { Icon } from './Icon'
import { SCREENS, type ScreenId } from '../lib/screens'
import { SignInButton, UserButton } from './AuthButtons'

interface LayoutShellProps {
  active: ScreenId
  onNav: (id: ScreenId) => void
  children: ReactNode
}

export function LayoutShell({ active, onNav, children }: LayoutShellProps) {
  const screenLabel = SCREENS.find((s) => s.id === active)?.label ?? ''

  return (
    <div data-component="LayoutShell">
      <aside data-component="Sidebar">
        <div data-element="brand">
          <span data-element="brandName">
            <span data-element="brandNu" aria-hidden="true">
              ν
            </span>
            ega
          </span>
          <span className="sr-only">Vega</span>
        </div>
        <nav data-element="nav" aria-label="Primary navigation">
          {SCREENS.map((s) => (
            <button
              key={s.id}
              type="button"
              data-element="navItem"
              data-active={active === s.id ? 'true' : 'false'}
              aria-current={active === s.id ? 'page' : undefined}
              aria-label={s.label}
              onClick={() => onNav(s.id)}
            >
              <Icon name={s.icon} size={20} />
              <span aria-hidden="true">{s.label}</span>
            </button>
          ))}
        </nav>
        <div data-element="footer" aria-label="Account">
          <UserButton />
          <AuthFooter />
        </div>
      </aside>

      <div className="tr-main">
        <header data-component="TopBar">
          <div data-element="crumbs">
            <span data-element="crumbMuted">Vega</span>
            <span data-element="crumbSep" aria-hidden="true">
              /
            </span>
            <span data-element="crumb">{screenLabel}</span>
          </div>
          <div data-element="actions">
            <button type="button" data-element="iconBtn" aria-label="Theme">
              <Icon name="moon" size={16} />
            </button>
            <button type="button" data-element="iconBtn" aria-label="Settings">
              <Icon name="settings" size={16} />
            </button>
          </div>
        </header>
        <main className="tr-page">{children}</main>
      </div>
    </div>
  )
}

function AuthFooter() {
  const { isAuthenticated } = useAuth0()
  if (isAuthenticated) return null
  return <SignInButton />
}
