/**
 * Top level application: layout shell wraps the active screen.
 * Sidebar nav controls which screen renders; only Pricing is wired
 * end to end in Phase 3, the other screens render Phase placeholders.
 */

import { useState, type JSX } from 'react'

import { LayoutShell } from './components/LayoutShell'
import { BacktestScreen } from './screens/BacktestScreen'
import { HeatMapScreen } from './screens/HeatMapScreen'
import { Placeholder } from './screens/Placeholder'
import { PricingScreen } from './screens/PricingScreen'
import type { ScreenId } from './lib/screens'

const PLACEHOLDER_PHASES: Partial<Record<ScreenId, { label: string; phase: number }>> = {
  compare: { label: 'Model Comparison', phase: 9 },
  history: { label: 'History', phase: 6 },
}

function App(): JSX.Element {
  const [active, setActive] = useState<ScreenId>('pricing')

  return (
    <LayoutShell active={active} onNav={setActive}>
      {active === 'pricing' && <PricingScreen />}
      {active === 'heatmap' && <HeatMapScreen />}
      {active === 'backtest' && <BacktestScreen />}
      {active !== 'pricing' && active !== 'heatmap' && active !== 'backtest' && (
        <Placeholder
          title={PLACEHOLDER_PHASES[active]!.label}
          phase={PLACEHOLDER_PHASES[active]!.phase}
        />
      )}
    </LayoutShell>
  )
}

export default App
