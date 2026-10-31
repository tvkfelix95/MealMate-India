const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const ACCESS_TOKEN_KEY = 'mealmate_access_token'

export type AuthSession = {
  access_token: string | null
  refresh_token: string | null
  email_confirmation_required?: boolean
}

type ApiError = Error & { status?: number }

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  const data = (await response.json().catch(() => ({}))) as { detail?: string; message?: string }
  if (!response.ok) {
    const error = new Error(data.detail ?? data.message ?? 'Something went wrong. Please try again.') as ApiError
    error.status = response.status
    throw error
  }
  return data as T
}

export function getAccessToken() {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY)
}

export function saveAccessToken(token: string) {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function clearAccessToken() {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
}

export function getApiErrorStatus(error: unknown) {
  return (error as ApiError).status
}

export function authenticate(email: string, password: string, mode: 'login' | 'register') {
  return request<AuthSession>(`/auth/${mode}`, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function bootstrapAdministrator(accessToken: string) {
  return request<{ message: string }>('/admin/bootstrap', {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
  })
}
