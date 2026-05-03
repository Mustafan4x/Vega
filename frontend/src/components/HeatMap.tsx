/**
 * Single heat map card. A 240x240 canvas paints the grid with a
 * bilinear interpolation across the underlying values, and a
 * transparent CSS grid overlay (`[data-element="hitGrid"]`) provides
 * one focusable, screen reader friendly cell per data point.
 *
 * Component anatomy mirrors the canonical reference at
 * ``docs/design/claude-design-output.html`` function ``HeatMap``:
 * card head, axis label, canvas frame, hit grid, x axis ticks. The
 * color stops live in ``src/lib/heatMapColors.ts`` so they stay
 * unit testable separately from this presentational layer.
 */

import { useEffect, useRef, type JSX } from 'react'

import { fmtUsd } from '../lib/format'
import { plColor, valueColor, type Rgb } from '../lib/heatMapColors'

export type HeatMapMode = 'value' | 'pl'
export type HeatMapDataComp = 'HeatMap' | 'PnlHeatMap'

interface HeatMapProps {
  dataComp: HeatMapDataComp
  title: string
  grid: ReadonlyArray<ReadonlyArray<number>>
  vAxis: ReadonlyArray<number>
  sAxis: ReadonlyArray<number>
  mode: HeatMapMode
  basis: number
}

const CANVAS_SIZE = 240

export function HeatMap({
  dataComp,
  title,
  grid,
  vAxis,
  sAxis,
  mode,
  basis,
}: HeatMapProps): JSX.Element {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rows = vAxis.length
  const cols = sAxis.length

  const flat = grid.flat()
  const min = flat.length > 0 ? Math.min(...flat) : 0
  const max = flat.length > 0 ? Math.max(...flat) : 1

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    canvas.width = CANVAS_SIZE
    canvas.height = CANVAS_SIZE
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    if (rows === 0 || cols === 0) {
      ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)
      return
    }

    const img = ctx.createImageData(CANVAS_SIZE, CANVAS_SIZE)
    const data = img.data
    const colorAt = (v: number): Rgb =>
      mode === 'value' ? valueColor(v, min, max) : plColor(v, basis)

    for (let py = 0; py < CANVAS_SIZE; py++) {
      const gy = (py / CANVAS_SIZE) * Math.max(rows - 1, 0)
      const y0 = Math.floor(gy)
      const y1 = Math.min(rows - 1, y0 + 1)
      const ty = gy - y0
      for (let px = 0; px < CANVAS_SIZE; px++) {
        const gx = (px / CANVAS_SIZE) * Math.max(cols - 1, 0)
        const x0 = Math.floor(gx)
        const x1 = Math.min(cols - 1, x0 + 1)
        const tx = gx - x0
        const v00 = grid[y0]?.[x0] ?? 0
        const v01 = grid[y0]?.[x1] ?? 0
        const v10 = grid[y1]?.[x0] ?? 0
        const v11 = grid[y1]?.[x1] ?? 0
        const top = v00 + (v01 - v00) * tx
        const bottom = v10 + (v11 - v10) * tx
        const v = top + (bottom - top) * ty
        const rgb = colorAt(v)
        const idx = (py * CANVAS_SIZE + px) * 4
        data[idx] = Math.round(rgb[0])
        data[idx + 1] = Math.round(rgb[1])
        data[idx + 2] = Math.round(rgb[2])
        data[idx + 3] = 255
      }
    }
    ctx.putImageData(img, 0, 0)
  }, [grid, vAxis, sAxis, rows, cols, mode, basis, min, max])

  const meta = mode === 'value' ? `${rows * cols} cells` : `basis ${fmtUsd(basis, 2)}`

  return (
    <section className="tr-card" data-component={dataComp}>
      <div className="tr-card-head">
        <h3 className="tr-card-title">{title}</h3>
        <span className="tr-card-meta">{meta}</span>
      </div>
      <div data-element="frame">
        <div data-element="axis" aria-hidden="true">
          <span data-element="axisLabel">sigma</span>
          {vAxis.map((s, i) => (
            <span key={i} data-element="tick">
              {(s * 100).toFixed(0)}
            </span>
          ))}
        </div>
        <div data-element="canvasWrap">
          <canvas
            ref={canvasRef}
            data-element="canvas"
            role="img"
            aria-label={`${title} heat map across ${rows} sigma rows and ${cols} spot columns`}
          />
          <div
            data-element="hitGrid"
            role="grid"
            aria-rowcount={rows}
            aria-colcount={cols}
            style={
              {
                '--rows': rows,
                '--cols': cols,
              } as React.CSSProperties
            }
          >
            {grid.map((row, ri) =>
              row.map((cell, ci) => {
                const sigma = vAxis[ri] ?? 0
                const spot = sAxis[ci] ?? 0
                const valueLabel = fmtUsd(cell, 2)
                const pl = cell - basis
                const cellLabel =
                  mode === 'value'
                    ? `Sigma ${(sigma * 100).toFixed(0)} percent, spot ${fmtUsd(spot, 0)}, value ${valueLabel}`
                    : `Sigma ${(sigma * 100).toFixed(0)} percent, spot ${fmtUsd(spot, 0)}, P&L ${fmtUsd(pl, 2)}`
                return (
                  <div
                    key={`${ri}-${ci}`}
                    data-element="cell"
                    role="gridcell"
                    tabIndex={-1}
                    title={cellLabel}
                    aria-label={cellLabel}
                  />
                )
              }),
            )}
          </div>
        </div>
      </div>
      <div data-element="axisX" aria-hidden="true">
        {sAxis.map((s, i) => (
          <span key={i} data-element="tick">
            {fmtUsd(s, 0)}
          </span>
        ))}
        <span data-element="axisLabel">spot</span>
      </div>
    </section>
  )
}
