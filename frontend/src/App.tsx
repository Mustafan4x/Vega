/**
 * Top level application: layout shell wraps the active screen.
 * Sidebar nav controls which screen renders; only Pricing is wired
 * end to end in Phase 3, the other screens render Phase placeholders.
 */

import { useState, type JSX } from 'react'

import { LayoutShell } from './components/LayoutShell'
import { Placeholder } from './screens/Placeholder'
import { PricingScreen } from './screens/PricingScreen'
import type { ScreenId } from './lib/screens'

const PLACEHOLDER_PHASES: Partial<Record<ScreenId, { label: string; phase: number }>> = {
  heatmap: { label: 'Heat Map', phase: 4 },
  compare: { label: 'Model Comparison', phase: 9 },
  backtest: { label: 'Backtest', phase: 10 },
  history: { label: 'History', phase: 6 },
}

function App(): JSX.Element {
  const [active, setActive] = useState<ScreenId>('pricing')

  return (
    <LayoutShell active={active} onNav={setActive}>
      {active === 'pricing' ? (
        <PricingScreen />
      ) : (
        <Placeholder
          title={PLACEHOLDER_PHASES[active]!.label}
          phase={PLACEHOLDER_PHASES[active]!.phase}
        />
      )}
    </LayoutShell>
  )
}

export default App
