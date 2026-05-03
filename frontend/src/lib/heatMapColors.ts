/**
 * Heat map color scale.
 *
 * Implements the segmented linear interpolator described in the
 * "Heat map color scale spec" section of
 * ``docs/design/wireframes.md``. Two modes:
 *
 *   value: 5 stop ramp (cool green to hot red), data range normalized
 *          dynamically as ``t = (v - min) / (max - min)``.
 *   pl:    diverging ramp anchored at zero P&L. Pl = v - basis. The
 *          normalizer is ``denom = max(0.5, basis * 0.4) * 3``, used
 *          as a soft scale so small basis cases (where 0.5 dollars
 *          dominates) and large basis cases both render gracefully.
 *
 * The exact RGB triples and stop counts are reproduced verbatim
 * from the canonical reference at
 * ``docs/design/claude-design-output.html`` (function ``HeatMap``).
 */

export type Rgb = readonly [number, number, number]

export const stopsValue: ReadonlyArray<Rgb> = [
  [16, 185, 129],
  [132, 204, 22],
  [234, 179, 8],
  [249, 115, 22],
  [239, 68, 68],
]

export const stopsNeg: ReadonlyArray<Rgb> = [
  [185, 28, 28],
  [239, 68, 68],
  [252, 165, 165],
  [229, 231, 235],
]

export const stopsPos: ReadonlyArray<Rgb> = [
  [229, 231, 235],
  [134, 239, 172],
  [34, 197, 94],
  [21, 128, 61],
]

function clamp01(t: number): number {
  if (!Number.isFinite(t)) return 0
  if (t < 0) return 0
  if (t > 1) return 1
  return t
}

function interpolate(stops: ReadonlyArray<Rgb>, t: number): Rgb {
  const tt = clamp01(t)
  const last = stops.length - 1
  const seg = Math.min(last - 1, Math.floor(tt * last))
  const lt = tt * last - seg
  const a = stops[seg]
  const b = stops[seg + 1]
  return [a[0] + (b[0] - a[0]) * lt, a[1] + (b[1] - a[1]) * lt, a[2] + (b[2] - a[2]) * lt]
}

export function valueColor(value: number, min: number, max: number): Rgb {
  const t = (value - min) / Math.max(0.0001, max - min)
  return interpolate(stopsValue, t)
}

export function plColor(value: number, basis: number): Rgb {
  const pl = value - basis
  const denom = Math.max(0.5, Math.abs(basis) * 0.4) * 3
  const tn = Math.max(-1, Math.min(1, pl / denom))
  if (tn <= 0) return interpolate(stopsNeg, tn + 1)
  return interpolate(stopsPos, tn)
}

export function rgbToCss(rgb: Rgb): string {
  const r = Math.round(rgb[0])
  const g = Math.round(rgb[1])
  const b = Math.round(rgb[2])
  return `rgb(${r}, ${g}, ${b})`
}
