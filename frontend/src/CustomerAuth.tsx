import { useState } from 'react'
import type { FormEvent } from 'react'

import { authenticate, getApiErrorStatus, saveAccessToken } from './lib/auth'

export type CustomerAuthMode = 'login' | 'register'

type CustomerAuthProps = {
  initialMode: CustomerAuthMode
  onBack: () => void
}

function CustomerAuth({ initialMode, onBack }: CustomerAuthProps) {
  const [mode, setMode] = useState<CustomerAuthMode>(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const session = await authenticate(email, password, mode)
      if (mode === 'register' && session.email_confirmation_required) {
        setSuccess('Account created. We sent a confirmation email. Verify your account, then log in.')
        setMode('login')
        setPassword('')
        return
      }

      if (!session.access_token) {
        setSuccess('Account created. Verify your email, then log in.')
        setMode('login')
        setPassword('')
        return
      }

      saveAccessToken(session.access_token)
      setSuccess(mode === 'login' ? 'You are logged in. Your preferences are ready to personalise.' : 'Account created successfully.')
      setPassword('')
    } catch (requestError) {
      const status = getApiErrorStatus(requestError)
      if (status === 409) {
        setError('This email is already registered. Try logging in instead.')
      } else if (status === 401) {
        setError('The email or password is incorrect. Please try again.')
      } else if (status === 403) {
        setError('Please verify your email address before continuing.')
      } else {
        setError(requestError instanceof Error ? requestError.message : 'Authentication is temporarily unavailable.')
      }
    } finally {
      setLoading(false)
    }
  }

  const switchMode = () => {
    setMode((current) => current === 'login' ? 'register' : 'login')
    setError('')
    setSuccess('')
  }

  return (
    <main className="min-h-screen bg-[#fffaf2] px-5 py-5 text-[#24352a] sm:px-8 sm:py-8">
      <div className="mx-auto max-w-2xl">
        <header className="flex items-center justify-between">
          <button onClick={onBack} className="flex items-center gap-2 text-lg font-bold tracking-tight" aria-label="Back to home">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#f28c5b] text-lg shadow-sm">✦</span>
            MealMate <span className="text-[#e47742]">India</span>
          </button>
          <button onClick={onBack} className="text-sm font-semibold text-[#718072] hover:text-[#e47742]">Back to home</button>
        </header>

        <section className="mt-12 rounded-[2rem] border border-[#edf0e8] bg-white p-6 shadow-[0_20px_50px_rgba(118,91,53,0.08)] sm:p-10">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-[#e47742]">Your MealMate account</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
          <p className="mt-3 leading-7 text-[#718072]">{mode === 'login' ? 'Log in to continue planning meals that fit your routine.' : 'Create an account to save your preferences and meal plans.'}</p>

          <form onSubmit={submit} className="mt-8 space-y-5">
            <div>
              <label className="text-sm font-bold text-[#48634e]" htmlFor="customer-email">Email address</label>
              <input id="customer-email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-2xl border border-[#dfe8dc] bg-[#fffdf8] p-4 outline-none focus:border-[#e47742] focus:ring-4 focus:ring-[#f9dfcc]" />
            </div>
            <div>
              <label className="text-sm font-bold text-[#48634e]" htmlFor="customer-password">Password</label>
              <input id="customer-password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required minLength={8} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-2xl border border-[#dfe8dc] bg-[#fffdf8] p-4 outline-none focus:border-[#e47742] focus:ring-4 focus:ring-[#f9dfcc]" />
              {mode === 'register' && <p className="mt-2 text-xs text-[#99a796]">Use 8 to 128 characters.</p>}
            </div>
            {error && <p role="alert" className="rounded-2xl bg-[#f8e9e2] p-4 text-sm font-semibold text-[#a74d35]">{error}</p>}
            {success && <p role="status" className="rounded-2xl bg-[#e8f0e4] p-4 text-sm font-semibold leading-6 text-[#416047]">{success}</p>}
            <button disabled={loading} className="w-full rounded-full bg-[#e47742] px-6 py-3.5 font-bold text-white shadow-[0_8px_20px_rgba(228,119,66,0.2)] transition hover:bg-[#d96632] disabled:cursor-wait disabled:opacity-60">
              {loading ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'}
            </button>
            <button type="button" onClick={switchMode} className="w-full text-sm font-bold text-[#537055] hover:text-[#e47742]">
              {mode === 'login' ? 'New to MealMate? Create an account' : 'Already have an account? Log in'}
            </button>
          </form>
        </section>
      </div>
    </main>
  )
}

export default CustomerAuth
