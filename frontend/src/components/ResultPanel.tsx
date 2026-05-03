/**
 * Right column of the pricing screen. Composes the call card and the
 * put card. The Greeks panel is reserved for Phase 7; until then the
 * grid renders a two cell row.
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

interface ResultPanelProps {
  inputs: PriceRequest
  result: PriceResponse | null
}

const ZERO_VALUES = { call: 0, put: 0 }

export function ResultPanel({ inputs, result }: ResultPanelProps): JSX.Element {
  const callValue = result?.call ?? ZERO_VALUES.call
  const putValue = result?.put ?? ZERO_VALUES.put
  const callI = computeCallIntrinsic(inputs.S, inputs.K)
  const putI = computePutIntrinsic(inputs.S, inputs.K)
  const callT = computeTimeValue(callValue, callI)
  const putT = computeTimeValue(putValue, putI)

  return (
    <section data-component="ResultPanel">
      <MetricCard
        variant="call"
        title="Call Value"
        value={callValue}
        intrinsic={callI}
        timeValue={callT}
      />
      <MetricCard
        variant="put"
        title="Put Value"
        value={putValue}
        intrinsic={putI}
        timeValue={putT}
      />
      <GreeksPanel title="Call Greeks" greeks={result?.call_greeks ?? null} />
      <GreeksPanel title="Put Greeks" greeks={result?.put_greeks ?? null} />
    </section>
  )
}
