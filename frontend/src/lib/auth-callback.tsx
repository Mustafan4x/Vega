import { useEffect, useRef, useState, type JSX } from 'react'
import { useAuth0 } from '@auth0/auth0-react'

import { saveCalculation, type HeatmapRequest } from './api'

interface PendingSave {
  request: HeatmapRequest
}

function isPendingSave(value: unknown): value is PendingSave {
  if (typeof value !== 'object' || value === null) return false
  const v = value as Record<string, unknown>
  return typeof v.request === 'object' && v.request !== null
}

export function AuthCallback(): JSX.Element {
  const { handleRedirectCallback, getAccessTokenSilently } = useAuth0()
  const [status, setStatus] = useState<'processing' | 'done' | 'error'>('processing')
  const ran = useRef(false)

  useEffect(() => {
    if (ran.current) return
    ran.current = true
    let cancelled = false

    const run = async () => {
      try {
        const result = await handleRedirectCallback()
        const appState = (result as { appState?: unknown } | undefined)?.appState
        const pending = (appState as { pendingSave?: unknown } | undefined)?.pendingSave
        if (isPendingSave(pending)) {
          const token = await getAccessTokenSilently()
          await saveCalculation(pending.request, { bearerToken: token })
        }
        if (cancelled) return
        window.history.replaceState({}, '', '/')
        setStatus('done')
      } catch {
        if (cancelled) return
        setStatus('error')
      }
    }

    void run()
    return () => {
      cancelled = true
    }
  }, [handleRedirectCallback, getAccessTokenSilently])

  if (status === 'error') {
    return <p>Sign-in failed. Please try again.</p>
  }
  return <p>Signing you in…</p>
}
