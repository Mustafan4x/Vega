/**
 * The screens the layout shell can render. Lives in its own module so
 * the LayoutShell component file only exports components (keeps Vite
 * Fast Refresh happy).
 *
 * "Compare" is not a separate screen: the Pricing screen toggles into
 * the side by side comparison view via ModelSelector. A History UI for
 * past calculations is a v2 idea (see docs/future-ideas.md).
 */

import type { IconName } from '../components/Icon'

export type ScreenId = 'pricing' | 'heatmap' | 'backtest'

export interface ScreenDef {
  id: ScreenId
  label: string
  icon: IconName
}

export const SCREENS: ReadonlyArray<ScreenDef> = [
  { id: 'pricing', label: 'Pricing', icon: 'calculator' },
  { id: 'heatmap', label: 'Heat Map', icon: 'grid-3x3' },
  { id: 'backtest', label: 'Backtest', icon: 'activity' },
]
