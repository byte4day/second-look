import type {
  AnalyzeResult,
  Debrief,
  DrillSession,
  DrillTurnResponse,
  FamilyContact,
  HelpNow,
  ReportSummary,
  Scenario,
  User,
} from './types.ts'

export const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

const TOKEN_KEY = 'scam_shield_token'

type BannerListener = (message: string | null) => void

let bannerListener: BannerListener | null = null

export function setApiErrorListener(listener: BannerListener) {
  bannerListener = listener
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

function extractErrorMessage(body: unknown, status: number): string {
  if (body && typeof body === 'object') {
    const b = body as Record<string, unknown>
    if (b.error && typeof b.error === 'object') {
      const err = b.error as { message_plain?: string }
      if (err.message_plain) return err.message_plain
    }
    if (b.detail && typeof b.detail === 'object') {
      const d = b.detail as { error?: { message_plain?: string }; message_plain?: string }
      if (d.error?.message_plain) return d.error.message_plain
      if (d.message_plain) return d.message_plain
    }
  }
  if (status === 429) return 'Too many requests. Wait a while and try again.'
  if (status >= 500) return 'The server is not available right now.'
  return 'Something went wrong.'
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = false,
): Promise<T> {
  const headers = new Headers(options.headers)
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (auth) {
    const token = getToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const text = await res.text()
  let json: unknown = null
  if (text) {
    try {
      json = JSON.parse(text) as unknown
    } catch {
      json = null
    }
  }

  if (!res.ok) {
    const message = extractErrorMessage(json, res.status)
    bannerListener?.(message)
    throw new Error(message)
  }

  return (json ?? {}) as T
}

export const api = {
  health: () => request<{ status: string }>('/api/health'),

  analyzeText: (text: string) =>
    request<AnalyzeResult>('/api/analyze/text', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  analyzeImage: (image_base64: string, mime_type: string) =>
    request<AnalyzeResult>('/api/analyze/image', {
      method: 'POST',
      body: JSON.stringify({
        image_base64,
        mime_type,
      }),
    }),

  listScenarios: () => request<Scenario[]>('/api/scenarios'),

  createDrill: (scenario_id: string, difficulty: string, mode: string) =>
    request<DrillSession>('/api/drills', {
      method: 'POST',
      body: JSON.stringify({ scenario_id, difficulty, mode }),
    }),

  drillTurn: (sessionId: string, message: string) =>
    request<DrillTurnResponse>(`/api/drills/${sessionId}/turns`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),

  finishDrill: (sessionId: string, hung_up: boolean) =>
    request<Debrief>(`/api/drills/${sessionId}/finish`, {
      method: 'POST',
      body: JSON.stringify({ hung_up }),
    }),

  helpNow: (region?: string) =>
    request<HelpNow>(
      `/api/content/help-now${region ? `?region=${encodeURIComponent(region)}` : ''}`,
    ),

  reportSummary: (area?: string) =>
    request<ReportSummary>(
      `/api/reports/summary${area ? `?area=${encodeURIComponent(area)}` : ''}`,
    ),

  createReport: (scam_type: string, area: string, text?: string) =>
    request<{ ok: boolean }>('/api/reports', {
      method: 'POST',
      body: JSON.stringify({ scam_type, area, text: text ?? null }),
    }),

  listFamily: () => request<FamilyContact[]>('/api/family', {}, true),

  addFamily: (name: string, email: string) =>
    request<FamilyContact>(
      '/api/family',
      { method: 'POST', body: JSON.stringify({ name, email }) },
      true,
    ),

  removeFamily: (contactId: number) =>
    request<{ ok: boolean }>(`/api/family/${contactId}`, { method: 'DELETE' }, true),

  acceptInvitation: (token: string) =>
    request<FamilyContact>(`/api/family/invitations/${encodeURIComponent(token)}/accept`, {
      method: 'POST',
    }),

  sendTestAlert: () =>
    request<{ ok: boolean }>('/api/alerts/test', { method: 'POST' }, true),

  sendAlert: (message_plain: string, contact_ids: number[]) =>
    request<{ sent: number; skipped: number }>(
      '/api/alerts',
      {
        method: 'POST',
        body: JSON.stringify({ message_plain, contact_ids }),
      },
      true,
    ),

  requestCode: (email: string) =>
    request<{ ok: boolean }>('/api/auth/request-code', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  verifyCode: (email: string, code: string) =>
    request<{ access_token: string }>('/api/auth/verify-code', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    }),

  me: () => request<User>('/api/me', {}, true),

  deleteMe: () => request<{ ok: boolean }>('/api/me', { method: 'DELETE' }, true),

  transcribeVoice: (file: Blob) => {
    const form = new FormData()
    form.append('file', file, 'voice.webm')
    return request<{ transcript: string }>('/api/voice/transcribe', {
      method: 'POST',
      body: form,
    })
  },
}