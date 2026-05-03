/**
 * Application shell: sidebar nav, sticky top bar, and a content slot.
 * Component anatomy mirrors the canonical reference at
 * ``docs/design/claude-design-output.html`` so designers can map between
 * the two by selector.
 */

import type { ReactNode } from 'react'

import { Icon } from './Icon'
import { SCREENS, type ScreenId } from '../lib/screens'

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
          <div data-element="brandMark" aria-hidden="true">
            <svg viewBox="0 0 64 64" width="22" height="22">
              <rect x="8" y="8" width="48" height="8" rx="1.5" fill="currentColor" />
              <rect x="28" y="8" width="8" height="48" rx="1.5" fill="currentColor" />
              <rect x="30" y="56" width="4" height="4" fill="currentColor" opacity="0.4" />
            </svg>
          </div>
          <span data-element="brandName">Trader</span>
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
              <Icon name={s.icon} size={16} />
              <span aria-hidden="true">{s.label}</span>
            </button>
          ))}
        </nav>
        <div data-element="footer" aria-label="Backend status: local">
          <span data-element="statusDot" aria-hidden="true" />
          <span aria-hidden="true">Local</span>
        </div>
      </aside>

      <div className="tr-main">
        <header data-component="TopBar">
          <div data-element="crumbs">
            <span data-element="crumbMuted">Trader</span>
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
            <div data-element="avatar" role="img" aria-label="Trader account">
              <span aria-hidden="true">TR</span>
            </div>
          </div>
        </header>
        <main className="tr-page">{children}</main>
      </div>
    </div>
  )
}
