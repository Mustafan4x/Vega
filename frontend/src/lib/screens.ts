/**
 * The five screens the layout shell can render. Lives in its own
 * module so the LayoutShell component file only exports components
 * (keeps Vite Fast Refresh happy).
 */

import type { IconName } from '../components/Icon'

export type ScreenId = 'pricing' | 'heatmap' | 'compare' | 'backtest' | 'history'

export interface ScreenDef {
  id: ScreenId
  label: string
  icon: IconName
}

export const SCREENS: ReadonlyArray<ScreenDef> = [
  { id: 'pricing', label: 'Pricing', icon: 'calculator' },
  { id: 'heatmap', label: 'Heat Map', icon: 'grid-3x3' },
  { id: 'compare', label: 'Model Comparison', icon: 'git-compare' },
  { id: 'backtest', label: 'Backtest', icon: 'activity' },
  { id: 'history', label: 'History', icon: 'history' },
]
