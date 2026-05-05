/**
 * One vertical result column for the Pricing screen: a MetricCard at the
 * top with the option's value, intrinsic, and time premium, plus its
 * GreeksPanel below. Rendered twice on the screen, once per side (call
 * and put), so each side gets its own column in the 4 column grid.
 */

import type { JSX } from 'react'

import { GreeksPanel } from './GreeksPanel'
import { MetricCard } from './MetricCard'
import {
  callIntrinsic as computeCallIntrinsic,
  putIntrinsic as computePutIntrinsic,
  timeValue as computeTimeValue,
} from '../lib/format'
import type { PriceRequest, PriceResponse } from '../lib/api'

interface ResultColumnProps {
  side: 'call' | 'put'
  inputs: PriceRequest
  result: PriceResponse | null
}

export function ResultColumn({ side, inputs, result }: ResultColumnProps): JSX.Element {
  const value = side === 'call' ? (result?.call ?? 0) : (result?.put ?? 0)
  const intrinsic =
    side === 'call'
      ? computeCallIntrinsic(inputs.S, inputs.K)
      : computePutIntrinsic(inputs.S, inputs.K)
  const time = computeTimeValue(value, intrinsic)
  const greeks = side === 'call' ? (result?.call_greeks ?? null) : (result?.put_greeks ?? null)
  const title = side === 'call' ? 'Call Value' : 'Put Value'
  const greeksTitle = side === 'call' ? 'Call Greeks' : 'Put Greeks'
  return (
    <>
      <MetricCard
        variant={side}
        title={title}
        value={value}
        intrinsic={intrinsic}
        timeValue={time}
      />
      <GreeksPanel title={greeksTitle} greeks={greeks} />
    </>
  )
}
