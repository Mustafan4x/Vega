/**
 * Single hero number card for one option leg (call or put).
 *
 * Variant tints the hero number: oxblood for call, sea green for put.
 * The intrinsic / time value sub line is the standard option price
 * decomposition (model price = intrinsic + time value).
 */

import type { JSX } from 'react'

import { Icon } from './Icon'
import { fmtUsd } from '../lib/format'

export type MetricVariant = 'call' | 'put'

interface MetricCardProps {
  variant: MetricVariant
  title: string
  value: number
  intrinsic: number
  timeValue: number
}

export function MetricCard({
  variant,
  title,
  value,
  intrinsic,
  timeValue,
}: MetricCardProps): JSX.Element {
  const inTheMoney = intrinsic > 0
  return (
    <div className="tr-card" data-component="MetricCard" data-variant={variant}>
      <div data-element="head">
        <span data-element="title">{title}</span>
        <span
          className={inTheMoney ? 'tr-tag tr-tag--success' : 'tr-tag tr-tag--danger'}
          data-element="tag"
          aria-label={inTheMoney ? 'In the money' : 'Out of the money'}
        >
          <Icon name={inTheMoney ? 'trending-up' : 'trending-down'} size={12} />
          <span aria-hidden="true">{inTheMoney ? 'ITM' : 'OTM'}</span>
        </span>
      </div>
      <div className="t-num-hero" data-element="hero">
        {fmtUsd(value, 4)}
      </div>
      <div data-element="sub">
        Intrinsic <span className="t-num">{fmtUsd(intrinsic, 2)}</span>
        <span data-element="dot" aria-hidden="true" />
        Time <span className="t-num">{fmtUsd(timeValue, 2)}</span>
      </div>
    </div>
  )
}
