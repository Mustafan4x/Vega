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

    const run = async () => {
      try {
        const result = await handleRedirectCallback()
        const appState = (result as { appState?: unknown } | undefined)?.appState
        const pending = (appState as { pendingSave?: unknown } | undefined)?.pendingSave
        if (isPendingSave(pending)) {
          const token = await getAccessTokenSilently()
          await saveCalculation(pending.request, { bearerToken: token })
        }
        window.history.replaceState({}, '', '/')
        // App.tsx tracks the active screen from window.location.pathname
        // and only updates on popstate. replaceState alone does not fire
        // popstate, so without this dispatch the App keeps rendering
        // <AuthCallback /> forever even after the URL is back to /.
        window.dispatchEvent(new PopStateEvent('popstate'))
        setStatus('done')
      } catch (err) {
        console.error('AuthCallback failed:', err)
        setStatus('error')
      }
    }

    void run()
  }, [handleRedirectCallback, getAccessTokenSilently])

  if (status === 'error') {
    return <p>Sign-in failed. Please try again.</p>
  }
  return <p>Signing you in…</p>
}
