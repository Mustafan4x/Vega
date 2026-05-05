/**
 * History screen.
 *
 * Lists previously saved heat map calculations newest first via
 * ``GET /api/calculations``. Selecting an entry loads its detail via
 * ``GET /api/calculations/{id}`` and renders the call and put grids
 * inline so the user can revisit a saved calculation without
 * re entering its inputs.
 */

import { useCallback, useEffect, useRef, useState, type JSX } from 'react'
import { useAuth0 } from '@auth0/auth0-react'

import { HeatMap } from '../components/HeatMap'
import { SignInButton } from '../components/AuthButtons'
import {
  fetchCalculation,
  fetchCalculations,
  PriceError,
  type CalculationDetail,
  type CalculationListResponse,
  type CalculationSummary,
} from '../lib/api'

const PAGE_SIZE = 20

type ListStatus =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'ready' }
  | { kind: 'error'; message: string }

type DetailStatus =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'ready' }
  | { kind: 'error'; message: string }

export function HistoryScreen(): JSX.Element {
  const { isAuthenticated, getAccessTokenSilently } = useAuth0()
  const [list, setList] = useState<CalculationListResponse | null>(null)
  const [listStatus, setListStatus] = useState<ListStatus>({ kind: 'idle' })
  const [selected, setSelected] = useState<CalculationDetail | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detailStatus, setDetailStatus] = useState<DetailStatus>({ kind: 'idle' })
  const inFlightList = useRef<AbortController | null>(null)
  const inFlightDetail = useRef<AbortController | null>(null)

  const loadList = useCallback(async () => {
    inFlightList.current?.abort()
    const controller = new AbortController()
    inFlightList.current = controller

    setListStatus({ kind: 'loading' })
    try {
      const token = await getAccessTokenSilently()
      const result = await fetchCalculations({
        limit: PAGE_SIZE,
        offset: 0,
        signal: controller.signal,
        bearerToken: token,
      })
      if (controller.signal.aborted) return
      setList(result)
      setListStatus({ kind: 'ready' })
    } catch (err) {
      if (controller.signal.aborted) return
      const message = err instanceof PriceError ? err.message : 'Could not load history.'
      setListStatus({ kind: 'error', message })
    }
  }, [getAccessTokenSilently])

  useEffect(() => {
    // Standard fetch-on-mount: loadList kicks off the network request
    // and updates state when it resolves. The lint rule warns about
    // setState inside an effect; here it is intentional and the
    // controller ref guards against late writes after unmount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadList()
    return () => {
      inFlightList.current?.abort()
      inFlightDetail.current?.abort()
    }
  }, [loadList])

  const onSelect = useCallback(
    async (id: string) => {
      inFlightDetail.current?.abort()
      const controller = new AbortController()
      inFlightDetail.current = controller

      setSelectedId(id)
      setDetailStatus({ kind: 'loading' })

      try {
        const token = await getAccessTokenSilently()
        const detail = await fetchCalculation(id, { signal: controller.signal, bearerToken: token })
        if (controller.signal.aborted) return
        setSelected(detail)
        setDetailStatus({ kind: 'ready' })
      } catch (err) {
        if (controller.signal.aborted) return
        const message = err instanceof PriceError ? err.message : 'Could not load that calculation.'
        setDetailStatus({ kind: 'error', message })
      }
    },
    [getAccessTokenSilently],
  )

  if (!isAuthenticated) {
    return (
      <section data-component="HistoryScreen">
        <div data-element="emptyState" className="tr-card">
          <h2 className="tr-card-title">Saved calculations</h2>
          <p>Sign in to see your saved calculations.</p>
          <SignInButton />
        </div>
      </section>
    )
  }

  return (
    <div className="tr-history-screen tr-screen-fade" data-component="HistoryScreen">
      <h1 className="sr-only">History</h1>

      <section className="tr-card" data-element="listCard">
        <div className="tr-card-head">
          <h2 className="tr-card-title">Saved calculations</h2>
          <span className="tr-card-meta" data-element="meta">
            {list ? `${list.total} total` : ''}
          </span>
        </div>

        {listStatus.kind === 'loading' && (
          <p className="tr-status" role="status">
            Loading history...
          </p>
        )}
        {listStatus.kind === 'error' && (
          <p className="tr-status tr-status--error" role="alert">
            {listStatus.message}
          </p>
        )}
        {listStatus.kind === 'ready' && list !== null && list.items.length === 0 && (
          <p className="tr-status" data-element="empty">
            No saved calculations yet. Save one from the Heat Map screen.
          </p>
        )}

        {list !== null && list.items.length > 0 && (
          <table className="tr-history-table" data-element="table">
            <thead>
              <tr>
                <th scope="col">Saved</th>
                <th scope="col">S</th>
                <th scope="col">K</th>
                <th scope="col">T</th>
                <th scope="col">sigma</th>
                <th scope="col">q</th>
                <th scope="col">Grid</th>
                <th scope="col"></th>
              </tr>
            </thead>
            <tbody>
              {list.items.map((row) => (
                <HistoryRow
                  key={row.calculation_id}
                  row={row}
                  selected={row.calculation_id === selectedId}
                  onSelect={onSelect}
                />
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="tr-card" data-element="detailCard">
        <div className="tr-card-head">
          <h2 className="tr-card-title">Selected calculation</h2>
          <span className="tr-card-meta" data-element="detailMeta">
            {selected !== null ? selected.calculation_id : ''}
          </span>
        </div>

        {detailStatus.kind === 'idle' && (
          <p className="tr-status">Pick a calculation from the list to view its grid.</p>
        )}
        {detailStatus.kind === 'loading' && (
          <p className="tr-status" role="status">
            Loading calculation...
          </p>
        )}
        {detailStatus.kind === 'error' && (
          <p className="tr-status tr-status--error" role="alert">
            {detailStatus.message}
          </p>
        )}
        {detailStatus.kind === 'ready' && selected !== null && (
          <>
            <dl className="tr-mono" data-element="detailInputs">
              <div data-pair="S">
                <dt>S</dt>
                <dd>{selected.s.toFixed(2)}</dd>
              </div>
              <div data-pair="K">
                <dt>K</dt>
                <dd>{selected.k.toFixed(2)}</dd>
              </div>
              <div data-pair="T">
                <dt>T</dt>
                <dd>{selected.t.toFixed(2)}</dd>
              </div>
              <div data-pair="r">
                <dt>r</dt>
                <dd>{(selected.r * 100).toFixed(1)}%</dd>
              </div>
              <div data-pair="q">
                <dt>q</dt>
                <dd>{(selected.q * 100).toFixed(1)}%</dd>
              </div>
              <div data-pair="sigma">
                <dt>sigma</dt>
                <dd>{(selected.sigma * 100).toFixed(1)}%</dd>
              </div>
            </dl>
            <div className="tr-heatmap-grids">
              <HeatMap
                dataComp="HeatMap"
                title="Call value"
                grid={selected.call}
                vAxis={selected.sigma_axis}
                sAxis={selected.spot_axis}
                mode="value"
                basis={0}
              />
              <HeatMap
                dataComp="PnlHeatMap"
                title="Put value"
                grid={selected.put}
                vAxis={selected.sigma_axis}
                sAxis={selected.spot_axis}
                mode="value"
                basis={0}
              />
            </div>
          </>
        )}
      </section>
    </div>
  )
}

interface HistoryRowProps {
  row: CalculationSummary
  selected: boolean
  onSelect: (id: string) => void
}

function HistoryRow({ row, selected, onSelect }: HistoryRowProps): JSX.Element {
  return (
    <tr data-element="row" data-selected={selected ? 'true' : 'false'}>
      <td>{formatTimestamp(row.created_at)}</td>
      <td className="tr-mono">{row.s.toFixed(2)}</td>
      <td className="tr-mono">{row.k.toFixed(2)}</td>
      <td className="tr-mono">{row.t.toFixed(2)}</td>
      <td className="tr-mono">{(row.sigma * 100).toFixed(1)}%</td>
      <td className="tr-mono" data-element="q">
        {(row.q * 100).toFixed(1)}%
      </td>
      <td className="tr-mono">
        {row.rows} x {row.cols}
      </td>
      <td>
        <button
          type="button"
          className="tr-btn tr-btn--ghost"
          onClick={() => onSelect(row.calculation_id)}
          aria-pressed={selected}
        >
          {selected ? 'Loaded' : 'Load'}
        </button>
      </td>
    </tr>
  )
}

function formatTimestamp(iso: string): string {
  if (iso === '') return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}
