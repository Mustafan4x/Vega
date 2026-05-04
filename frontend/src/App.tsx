/**
 * Top level application: layout shell wraps the active screen.
 * Sidebar nav controls which screen renders.
 *
 * "Compare" reuses PricingScreen with `initialCompare={true}` and a
 * distinct React key so swapping nav items remounts the screen and
 * the toggle starts in the right state.
 */

import { useState, type JSX } from 'react'

import { LayoutShell } from './components/LayoutShell'
import { BacktestScreen } from './screens/BacktestScreen'
import { HeatMapScreen } from './screens/HeatMapScreen'
import { HistoryScreen } from './screens/HistoryScreen'
import { PricingScreen } from './screens/PricingScreen'
import type { ScreenId } from './lib/screens'

function App(): JSX.Element {
  const [active, setActive] = useState<ScreenId>('pricing')

  return (
    <LayoutShell active={active} onNav={setActive}>
      {active === 'pricing' && <PricingScreen key="pricing" />}
      {active === 'compare' && <PricingScreen key="compare" initialCompare={true} />}
      {active === 'heatmap' && <HeatMapScreen />}
      {active === 'backtest' && <BacktestScreen />}
      {active === 'history' && <HistoryScreen />}
    </LayoutShell>
  )
}

export default App
