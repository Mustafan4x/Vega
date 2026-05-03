/**
 * Number formatting helpers. All numbers in the UI are typeset in
 * Newsreader with tabular figures (see ``.t-num`` rules in
 * ``src/styles/components.css``); these helpers handle the value side.
 */

const usdFormatters = new Map<number, Intl.NumberFormat>()

function getUsdFormatter(decimals: number): Intl.NumberFormat {
  let f = usdFormatters.get(decimals)
  if (!f) {
    f = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
    usdFormatters.set(decimals, f)
  }
  return f
}

export function fmtUsd(value: number, decimals: number = 2): string {
  if (!Number.isFinite(value)) return '—'
  return getUsdFormatter(decimals).format(value)
}

export function fmtNumber(value: number, decimals: number = 2): string {
  if (!Number.isFinite(value)) return '—'
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function callIntrinsic(S: number, K: number): number {
  return Math.max(0, S - K)
}

export function putIntrinsic(S: number, K: number): number {
  return Math.max(0, K - S)
}

export function timeValue(modelPrice: number, intrinsic: number): number {
  return Math.max(0, modelPrice - intrinsic)
}
