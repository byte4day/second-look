import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { PractiseChat } from '../pages/PractiseChat.tsx'

vi.mock('../api/client.ts', () => ({
  API_BASE: 'http://test',
  api: {
    drillTurn: vi.fn(async (_id: string, message: string) => ({
      user_turn: { id: 1, role: 'you', content: message },
      caller_turn: { id: 2, role: 'caller', content: 'Read me the code we just sent.' },
      finished: false,
      warning: null,
    })),
    finishDrill: vi.fn(),
    transcribeVoice: vi.fn(),
  },
}))

function renderChat() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/practise/chat/s1']}>
        <Routes>
          <Route path="/practise/chat/:sessionId" element={<PractiseChat />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('PractiseChat', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.setItem('scam_shield_caller_voice', '0')
    sessionStorage.setItem(
      'drill_s1',
      JSON.stringify({
        id: 's1',
        scenario_id: 'bank_otp',
        difficulty: 'easy',
        mode: 'experience',
        status: 'active',
        turn_count: 1,
        turns: [{ id: 0, role: 'caller', content: 'Hello, this is your bank.' }],
      }),
    )
  })

  it('keeps the whole conversation after a refresh', async () => {
    const first = renderChat()
    expect(screen.getByText('Hello, this is your bank.')).toBeInTheDocument()

    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Who is this?' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    await waitFor(() => screen.getByText('Read me the code we just sent.'))

    // Simulate a page refresh: unmount and mount again from sessionStorage.
    first.unmount()
    renderChat()

    expect(screen.getByText('Hello, this is your bank.')).toBeInTheDocument()
    expect(screen.getByText('Who is this?')).toBeInTheDocument()
    expect(screen.getByText('Read me the code we just sent.')).toBeInTheDocument()
    const saved = JSON.parse(sessionStorage.getItem('drill_s1') ?? '{}')
    expect(saved.scenario_id).toBe('bank_otp')
    expect(saved.turns).toHaveLength(3)
  })
})
