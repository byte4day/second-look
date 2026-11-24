import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { axe } from 'vitest-axe'
import { Practise } from '../pages/Practise.tsx'

vi.mock('../api/client.ts', () => ({
  api: {
    listScenarios: vi.fn(async () => [
      {
        id: 'bank_otp',
        title: 'Fake bank fraud call',
        plain_description: 'A caller pretends to be your bank.',
        scammer_goal: 'code',
        opening_message: 'Hello',
        tactics: [],
        payment_method: 'none',
        red_flags_expected: [],
        difficulty_variants: {},
        max_turns: 6,
      },
    ]),
    createDrill: vi.fn(),
  },
}))

function renderPractise() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Practise />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Practise', () => {
  it('offers one-tap bank fraud quick start', async () => {
    renderPractise()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start the bank fraud practice now/i })).toBeInTheDocument()
    })
  })

  it('has no serious axe violations', async () => {
    const { container } = renderPractise()
    await waitFor(() => screen.getByRole('button', { name: /start the bank fraud practice now/i }))
    const results = await axe(container)
    const serious = results.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious')
    expect(serious).toEqual([])
  })
})
