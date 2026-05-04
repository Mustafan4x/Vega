/**
 * Top level application: layout shell wraps the active screen.
 * Sidebar nav controls which screen renders.
 */

import { useState, type JSX } from 'react'

import { LayoutShell } from './components/LayoutShell'
import { BacktestScreen } from './screens/BacktestScreen'
import { HeatMapScreen } from './screens/HeatMapScreen'
import { PricingScreen } from './screens/PricingScreen'
import type { ScreenId } from './lib/screens'

function App(): JSX.Element {
  const [active, setActive] = useState<ScreenId>('pricing')

  return (
    <LayoutShell active={active} onNav={setActive}>
      {active === 'pricing' && <PricingScreen />}
      {active === 'heatmap' && <HeatMapScreen />}
      {active === 'backtest' && <BacktestScreen />}
    </LayoutShell>
  )
}

export default App
