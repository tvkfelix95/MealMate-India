import { useState } from 'react'
import type { FormEvent } from 'react'

import {
  authenticate,
  bootstrapAdministrator,
  clearAccessToken,
  getAccessToken,
  getApiErrorStatus,
  saveAccessToken,
} from './lib/auth'

type AdminSetupProps = { onBack: () => void }
type AuthMode = 'login' | 'register'
type SetupStatus = 'idle' | 'success' | 'unavailable' | 'session-expired'

function AdminSetup({ onBack }: AdminSetupProps) {
  const [mode, setMode] = useState<AuthMode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [accessToken, setAccessToken] = useState(getAccessToken())
  const [loading, setLoading] = useState(false)
  const [authError, setAuthError] = useState('')
  const [setupStatus, setSetupStatus] = useState<SetupStatus>('idle')
  const [setupError, setSetupError] = useState('')

  const submitAuth = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    setAuthError('')
    setSetupStatus('idle')
    try {
      const session = await authenticate(email, password, mode)
      if (!session.access_token) {
        setAuthError('Registration received. Confirm your email, then log in to continue.')
        return
      }
      saveAccessToken(session.access_token)
      setAccessToken(session.access_token)
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Authentication failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const setupAdministrator = async () => {
    if (!accessToken) return
    setLoading(true)
    setSetupError('')
    setSetupStatus('idle')
    try {
      await bootstrapAdministrator(accessToken)
      setSetupStatus('success')
    } catch (error) {
      if (getApiErrorStatus(error) === 401) {
        clearAccessToken()
        setAccessToken(null)
        setSetupStatus('session-expired')
      } else if (getApiErrorStatus(error) === 403) {
        setSetupStatus('unavailable')
      } else {
        setSetupError(error instanceof Error ? error.message : 'Setup is temporarily unavailable.')
      }
    } finally {
      setLoading(false)
    }
  }

  const signOutLocally = () => {
    clearAccessToken()
    setAccessToken(null)
    setSetupStatus('idle')
  }

  return (
    <main className="min-h-screen bg-[#fffaf2] px-5 py-5 text-[#24352a] sm:px-8 sm:py-8">
      <div className="mx-auto max-w-2xl">
        <header className="flex items-center justify-between">
          <a className="flex items-center gap-2 text-lg font-bold tracking-tight" href="#top">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#f28c5b] text-lg shadow-sm">✦</span>
            MealMate <span className="text-[#e47742]">India</span>
          </a>
          <button onClick={onBack} className="text-sm font-semibold text-[#718072] hover:text-[#e47742]">
            Back to home
          </button>
        </header>

        <section className="mt-12 rounded-[2rem] border border-[#edf0e8] bg-white p-6 shadow-[0_20px_50px_rgba(118,91,53,0.08)] sm:p-10">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-[#e47742]">Trusted setup</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">Set up administrator account</h1>
          <p className="mt-3 leading-7 text-[#718072]">
            Sign in with the confirmed account chosen for MealMate India. Only the configured first administrator can complete this one-time setup.
          </p>

          {!accessToken ? (
            <form onSubmit={submitAuth} className="mt-8 space-y-5">
              <div>
                <label className="text-sm font-bold text-[#48634e]" htmlFor="admin-email">Email address</label>
                <input id="admin-email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-2xl border border-[#dfe8dc] bg-[#fffdf8] p-4 outline-none focus:border-[#e47742] focus:ring-4 focus:ring-[#f9dfcc]" />
              </div>
              <div>
                <label className="text-sm font-bold text-[#48634e]" htmlFor="admin-password">Password</label>
                <input id="admin-password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-2xl border border-[#dfe8dc] bg-[#fffdf8] p-4 outline-none focus:border-[#e47742] focus:ring-4 focus:ring-[#f9dfcc]" />
              </div>
              {authError && <p role="alert" className="rounded-2xl bg-[#f8e9e2] p-4 text-sm font-semibold text-[#a74d35]">{authError}</p>}
              <button disabled={loading} className="w-full rounded-full bg-[#e47742] px-6 py-3.5 font-bold text-white shadow-[0_8px_20px_rgba(228,119,66,0.2)] transition hover:bg-[#d96632] disabled:cursor-wait disabled:opacity-60">
                {loading ? 'Please wait…' : mode === 'login' ? 'Log in securely' : 'Register securely'}
              </button>
              <button type="button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setAuthError('') }} className="w-full text-sm font-bold text-[#537055] hover:text-[#e47742]">
                {mode === 'login' ? 'Need to register first?' : 'Already registered? Log in'}
              </button>
            </form>
          ) : (
            <div className="mt-8">
              <div className="rounded-2xl bg-[#f5f8f1] p-4 text-sm font-semibold text-[#537055]">You are signed in. Your session is ready for the one-time administrator check.</div>
              <button onClick={setupAdministrator} disabled={loading} className="mt-5 w-full rounded-full bg-[#e47742] px-6 py-3.5 font-bold text-white shadow-[0_8px_20px_rgba(228,119,66,0.2)] transition hover:bg-[#d96632] disabled:cursor-wait disabled:opacity-60">
                {loading ? 'Checking setup…' : 'Set up administrator account'}
              </button>
              <button onClick={signOutLocally} className="mt-4 w-full text-sm font-bold text-[#718072] hover:text-[#e47742]">Use a different account</button>
            </div>
          )}

          {setupStatus === 'success' && <div role="status" className="mt-6 rounded-2xl bg-[#e8f0e4] p-4 text-sm font-semibold text-[#416047]">Administrator setup completed successfully. You can now use protected administrator tools.</div>}
          {setupStatus === 'unavailable' && <div role="alert" className="mt-6 rounded-2xl bg-[#fff3df] p-4 text-sm font-semibold leading-6 text-[#8a5b2a]">Administrator setup is unavailable for this account. The account may not be the configured first-admin account, or setup may already be complete.</div>}
          {setupStatus === 'session-expired' && <div role="alert" className="mt-6 rounded-2xl bg-[#f8e9e2] p-4 text-sm font-semibold text-[#a74d35]">Your session has expired. Please log in again to continue.</div>}
          {setupError && <div role="alert" className="mt-6 rounded-2xl bg-[#f8e9e2] p-4 text-sm font-semibold text-[#a74d35]">{setupError}</div>}
        </section>
      </div>
    </main>
  )
}

export default AdminSetup
