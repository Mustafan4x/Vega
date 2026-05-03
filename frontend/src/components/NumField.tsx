/**
 * Labeled numeric input with an optional unit suffix.
 *
 * Allows free typing of a partial decimal (e.g. ``-0.``) so the user can
 * compose a value without the field jumping under their cursor; on blur
 * the draft is parsed and clamped to a finite number, falling back to
 * the supplied ``min`` (or 0 if no min is provided) when parsing fails.
 *
 * The label and input are linked via ``htmlFor`` and ``id`` for screen
 * readers; the suffix is rendered as decorative text and is presented to
 * assistive tech via the input's ``aria-describedby``.
 */

import { useEffect, useId, useRef, useState, type JSX } from 'react'

interface NumFieldProps {
  label: string
  value: number
  onChange: (next: number) => void
  suffix?: string
  min?: number
  step?: string
  invalid?: boolean
  describedBy?: string
}

const PARTIAL_DECIMAL = /^-?\d*\.?\d*$/

export function NumField({
  label,
  value,
  onChange,
  suffix,
  min,
  step = 'any',
  invalid = false,
  describedBy,
}: NumFieldProps): JSX.Element {
  const inputId = useId()
  const suffixId = useId()
  const focused = useRef(false)
  const [draft, setDraft] = useState<string>(() => formatInitial(value))

  useEffect(() => {
    if (!focused.current) setDraft(formatInitial(value))
  }, [value])

  const ariaDescribedBy =
    [describedBy, suffix ? suffixId : undefined].filter(Boolean).join(' ') || undefined

  return (
    <div data-element="row">
      <label className="tr-label" htmlFor={inputId}>
        {label}
      </label>
      <div className="tr-input-wrap">
        <input
          id={inputId}
          type="text"
          inputMode="decimal"
          autoComplete="off"
          spellCheck={false}
          step={step}
          className="tr-input tr-mono"
          value={draft}
          aria-invalid={invalid}
          aria-describedby={ariaDescribedBy}
          onFocus={() => {
            focused.current = true
          }}
          onBlur={() => {
            focused.current = false
            const parsed = parseFloat(draft)
            const clean = Number.isFinite(parsed) ? clamp(parsed, min) : (min ?? 0)
            setDraft(clean.toString())
            onChange(clean)
          }}
          onChange={(e) => {
            const raw = e.target.value
            if (raw === '' || PARTIAL_DECIMAL.test(raw)) {
              setDraft(raw)
              const n = parseFloat(raw)
              if (Number.isFinite(n)) onChange(clamp(n, min))
            }
          }}
        />
        {suffix && (
          <span id={suffixId} className="tr-suffix" data-element="suffix">
            {suffix}
          </span>
        )}
      </div>
    </div>
  )
}

function formatInitial(value: number): string {
  if (!Number.isFinite(value)) return '0'
  return value.toString()
}

function clamp(n: number, min?: number): number {
  if (typeof min === 'number' && n < min) return min
  return n
}
