/**
 * Placeholder screen used for nav targets that have not landed yet
 * (Heat Map, Model Comparison, Backtest, History). Rendered only so
 * the sidebar nav is wired end to end in Phase 3.
 */

import type { JSX } from 'react'

interface PlaceholderProps {
  title: string
  phase: number
}

export function Placeholder({ title, phase }: PlaceholderProps): JSX.Element {
  return (
    <div className="tr-screen-fade">
      <section className="tr-card">
        <div className="tr-card-head">
          <h2 className="tr-card-title">{title}</h2>
          <span className="tr-card-meta">Coming in Phase {phase}</span>
        </div>
        <div className="tr-placeholder">
          {title} lands in Phase {phase}.
        </div>
      </section>
    </div>
  )
}
