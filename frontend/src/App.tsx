/**
 * Top level application: layout shell wraps the active screen.
 * Sidebar nav controls which screen renders.
 */

import { useState, useEffect, type JSX } from 'react'

import { LayoutShell } from './components/LayoutShell'
import { BacktestScreen } from './screens/BacktestScreen'
import { HeatMapScreen } from './screens/HeatMapScreen'
import { HistoryScreen } from './screens/HistoryScreen'
import { PricingScreen } from './screens/PricingScreen'
import { AuthCallback } from './lib/auth-callback'
import type { ScreenId } from './lib/screens'

function App(): JSX.Element {
  const [active, setActive] = useState<ScreenId>('pricing')
  const [path, setPath] = useState<string>(window.location.pathname)

  useEffect(() => {
    const onPop = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  if (path === '/callback') {
    return <AuthCallback />
  }

  return (
    <LayoutShell active={active} onNav={setActive}>
      {active === 'pricing' && <PricingScreen />}
      {active === 'heatmap' && <HeatMapScreen />}
      {active === 'backtest' && <BacktestScreen />}
      {active === 'history' && <HistoryScreen />}
    </LayoutShell>
  )
}

export default App
