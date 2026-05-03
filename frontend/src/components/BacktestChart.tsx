/**
 * P&L line chart for the backtest result. Inline SVG, no third party
 * library, matching the Oxblood reference's rendering style. The
 * single line traces the cumulative P&L over the held series; the
 * zero P&L horizontal axis is rendered as a subtle gridline so the
 * sign of the curve is unambiguous at a glance.
 */

import type { JSX } from 'react'

import type { BacktestResponse } from '../lib/api'

interface BacktestChartProps {
  result: BacktestResponse | null
  width?: number
  height?: number
}

const PADDING = { top: 16, right: 16, bottom: 28, left: 56 }

export function BacktestChart({
  result,
  width = 720,
  height = 280,
}: BacktestChartProps): JSX.Element {
  if (result === null || result.dates.length < 2) {
    return (
      <section className="tr-card" data-component="BacktestChart">
        <div className="tr-card-head">
          <h2 className="tr-card-title">P&amp;L curve</h2>
          <span className="tr-card-meta">awaiting backtest</span>
        </div>
        <div className="tr-placeholder" data-element="empty">
          Run a backtest to see its P&amp;L curve here.
        </div>
      </section>
    )
  }

  const innerW = width - PADDING.left - PADDING.right
  const innerH = height - PADDING.top - PADDING.bottom

  const xs = result.pnl.map((_, i) => i)
  const minX = 0
  const maxX = xs[xs.length - 1]
  const minY = Math.min(0, ...result.pnl)
  const maxY = Math.max(0, ...result.pnl)
  const yPad = (maxY - minY) * 0.1 || 1
  const yLo = minY - yPad
  const yHi = maxY + yPad

  const xScale = (x: number) => PADDING.left + (innerW * (x - minX)) / Math.max(maxX - minX, 1e-9)
  const yScale = (y: number) =>
    PADDING.top + innerH - (innerH * (y - yLo)) / Math.max(yHi - yLo, 1e-9)

  const points = result.pnl
    .map((y, i) => `${xScale(xs[i]).toFixed(1)},${yScale(y).toFixed(1)}`)
    .join(' ')

  const zeroY = yScale(0)
  const finalPnl = result.pnl[result.pnl.length - 1]
  const positive = finalPnl >= 0

  // Six y axis ticks evenly spaced.
  const yTicks: number[] = []
  for (let i = 0; i <= 4; i++) {
    yTicks.push(yLo + ((yHi - yLo) * i) / 4)
  }
  const xTicks = pickXTicks(result.dates)

  return (
    <section className="tr-card" data-component="BacktestChart">
      <div className="tr-card-head">
        <h2 className="tr-card-title">P&amp;L curve</h2>
        <span className="tr-card-meta" data-element="finalPnl">
          {result.symbol} {result.strategy.replace('_', ' ')} · final {formatDollars(finalPnl)}
        </span>
      </div>
      <div data-element="canvas">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          width="100%"
          role="img"
          aria-label={`P&L curve for ${result.symbol} ${result.strategy} from ${result.entry_date} to ${result.expiry_date}, final P&L ${formatDollars(finalPnl)}`}
        >
          <line
            x1={PADDING.left}
            x2={width - PADDING.right}
            y1={zeroY}
            y2={zeroY}
            stroke="currentColor"
            strokeOpacity="0.18"
            strokeDasharray="4 4"
          />
          {yTicks.map((t) => (
            <g key={`y-${t}`}>
              <line
                x1={PADDING.left}
                x2={width - PADDING.right}
                y1={yScale(t)}
                y2={yScale(t)}
                stroke="currentColor"
                strokeOpacity="0.06"
              />
              <text
                x={PADDING.left - 8}
                y={yScale(t)}
                textAnchor="end"
                dominantBaseline="middle"
                fontFamily="var(--font-number)"
                fontSize="11"
                fill="currentColor"
                fillOpacity="0.55"
              >
                {formatDollars(t)}
              </text>
            </g>
          ))}
          {xTicks.map(({ index, label }) => (
            <text
              key={`x-${index}`}
              x={xScale(index)}
              y={height - 10}
              textAnchor="middle"
              fontFamily="var(--font-number)"
              fontSize="11"
              fill="currentColor"
              fillOpacity="0.55"
            >
              {label}
            </text>
          ))}
          <polyline
            points={points}
            fill="none"
            stroke={positive ? 'var(--color-accent-500)' : 'var(--color-primary-500)'}
            strokeWidth="2"
            strokeLinejoin="round"
            strokeLinecap="round"
            data-element="pnlLine"
          />
        </svg>
      </div>
    </section>
  )
}

function pickXTicks(dates: string[]): { index: number; label: string }[] {
  const n = dates.length
  if (n === 0) return []
  const targetCount = Math.min(5, n)
  const result: { index: number; label: string }[] = []
  for (let i = 0; i < targetCount; i++) {
    const idx = Math.floor((i * (n - 1)) / Math.max(targetCount - 1, 1))
    const label = dates[idx].slice(5) // mm-dd
    result.push({ index: idx, label })
  }
  return result
}

function formatDollars(n: number): string {
  const sign = n < 0 ? '-' : ''
  const abs = Math.abs(n)
  return `${sign}$${abs.toFixed(2)}`
}
