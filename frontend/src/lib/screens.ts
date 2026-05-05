/**
 * The screens the layout shell can render. Lives in its own module so
 * the LayoutShell component file only exports components (keeps Vite
 * Fast Refresh happy).
 *
 * Compare-all-models lives as a toggle on the Pricing screen, not as
 * its own nav item. "History" lists previously saved heat map
 * calculations and lets the user reload one.
 */

import type { IconName } from '../components/Icon'

export type ScreenId = 'pricing' | 'heatmap' | 'backtest' | 'history'

export interface ScreenDef {
  id: ScreenId
  label: string
  icon: IconName
}

export const SCREENS: ReadonlyArray<ScreenDef> = [
  { id: 'pricing', label: 'Pricing', icon: 'calculator' },
  { id: 'heatmap', label: 'Heat Map', icon: 'grid-3x3' },
  { id: 'backtest', label: 'Backtest', icon: 'activity' },
  { id: 'history', label: 'History', icon: 'history' },
]
