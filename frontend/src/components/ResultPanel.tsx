/**
 * Right column of the pricing screen. Composes the call card and the
 * put card. The Greeks panel is reserved for Phase 7; until then the
 * grid renders a two cell row.
 */

import type { JSX } from 'react'

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

const ZERO_RESULT: PriceResponse = { call: 0, put: 0 }

export function ResultPanel({ inputs, result }: ResultPanelProps): JSX.Element {
  const r = result ?? ZERO_RESULT
  const callI = computeCallIntrinsic(inputs.S, inputs.K)
  const putI = computePutIntrinsic(inputs.S, inputs.K)
  const callT = computeTimeValue(r.call, callI)
  const putT = computeTimeValue(r.put, putI)

  return (
    <section data-component="ResultPanel">
      <MetricCard
        variant="call"
        title="Call Value"
        value={r.call}
        intrinsic={callI}
        timeValue={callT}
      />
      <MetricCard variant="put" title="Put Value" value={r.put} intrinsic={putI} timeValue={putT} />
    </section>
  )
}
