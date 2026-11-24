import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { axe } from 'vitest-axe'
import { CheckMessage } from '../pages/CheckMessage.tsx'

vi.mock('../api/client.ts', () => ({
  api: {
    analyzeText: vi.fn(async () => ({
      risk_level: 'likely_scam',
      headline: 'Fake bank alert',
      reasons: [{ flag: 'URGENCY', quote: 'reply YES or NO', why: 'Pushes a quick reply.' }],
      what_to_do_now: ['Do not reply'],
      what_not_to_do: ['Do not share codes'],
      note: 'If unsure, use a number you know.',
    })),
    extractTextFromImage: vi.fn(),
  },
}))

function renderCheck() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false }, queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <CheckMessage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('CheckMessage', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('fills scam sample into the message box', async () => {
    const user = userEvent.setup()
    renderCheck()
    await user.click(screen.getByRole('button', { name: /use a scam text/i }))
    const area = screen.getByLabelText(/message text/i) as HTMLTextAreaElement
    expect(area.value).toMatch(/Chase Fraud/)
  })

  it('has no serious axe violations', async () => {
    const { container } = renderCheck()
    const results = await axe(container)
    const serious = results.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious')
    expect(serious).toEqual([])
  })
})
