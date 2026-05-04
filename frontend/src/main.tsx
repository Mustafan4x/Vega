import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Auth0Provider } from '@auth0/auth0-react'

import './index.css'
import App from './App.tsx'

function readVar(name: string, required: boolean): string {
  const value = (import.meta.env as Record<string, string | undefined>)[name] ?? ''
  const trimmed = typeof value === 'string' ? value.trim() : ''
  if (required && import.meta.env.PROD && trimmed === '') {
    throw new Error(
      `${name} is not set. Production builds require all VITE_AUTH0_* env vars; ` +
        'see docs/setup-guide.md (Auth0 setup).',
    )
  }
  return trimmed
}

const domain = readVar('VITE_AUTH0_DOMAIN', true)
const clientId = readVar('VITE_AUTH0_CLIENT_ID', true)
const audience = readVar('VITE_AUTH0_AUDIENCE', false) || 'vega-api'
const redirectUri =
  readVar('VITE_AUTH0_REDIRECT_URI', false) || `${window.location.origin}/callback`

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        audience,
        redirect_uri: redirectUri,
      }}
      useRefreshTokens={true}
      cacheLocation="memory"
    >
      <App />
    </Auth0Provider>
  </StrictMode>,
)
