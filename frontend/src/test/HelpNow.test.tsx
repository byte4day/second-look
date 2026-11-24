import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { axe } from 'vitest-axe'
import { HelpNow } from '../pages/HelpNow.tsx'

vi.mock('../api/client.ts', () => ({
  api: {
    helpNow: vi.fn(async () => ({
      id: 'uk-example',
      label: 'United Kingdom',
      help_now_steps: ['Stop talking to the person.', 'Hang up or close the chat.'],
      who_to_contact: [
        {
          name: 'Action Fraud',
          how: 'Report fraud.',
          url: 'https://www.actionfraud.police.uk/',
          phone: '0300 123 2040',
        },
      ],
    })),
  },
}))

vi.mock('../hooks/useSpeech.ts', () => ({
  useSpeech: () => ({ available: false, speak: vi.fn() }),
}))

function renderHelp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <HelpNow />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('HelpNow', () => {
  it('shows verified Action Fraud number', async () => {
    renderHelp()
    await waitFor(() => {
      expect(screen.getByText('0300 123 2040')).toBeInTheDocument()
    })
    expect(screen.queryByText(/TODO/i)).not.toBeInTheDocument()
  })

  it('has no serious axe violations', async () => {
    const { container } = renderHelp()
    await waitFor(() => screen.getByText('0300 123 2040'))
    const results = await axe(container)
    const serious = results.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious')
    expect(serious).toEqual([])
  })
})
