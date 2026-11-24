import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { axe } from 'vitest-axe'
import { Result } from '../pages/Result.tsx'

vi.mock('../hooks/useSpeech.ts', () => ({
  useSpeech: () => ({ available: false, speak: vi.fn() }),
}))

const sample = {
  result: {
    risk_level: 'likely_scam' as const,
    headline: 'Possible scam text about a large check',
    reasons: [
      { flag: 'AUTHORITY_CLAIM', quote: 'Chase Fraud', why: 'Pretends to be a bank.' },
    ],
    what_to_do_now: ['Do not reply', 'Call your bank using the number on your card'],
    what_not_to_do: ['Do not share codes'],
    note: 'If you are unsure, contact them using a number you already know.',
  },
  source: 'Chase Fraud: Did you write a check for $5,000.00?',
}

describe('Result', () => {
  beforeEach(() => {
    sessionStorage.setItem('scam_shield_last_result', JSON.stringify(sample.result))
    sessionStorage.setItem('scam_shield_last_source', sample.source)
  })

  it('shows risk label and next steps', () => {
    render(
      <MemoryRouter>
        <Result />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: /possible scam text/i })).toBeInTheDocument()
    expect(screen.getByText(/likely a scam/i)).toBeInTheDocument()
    expect(screen.getByText(/do not reply/i)).toBeInTheDocument()
  })

  it('has no serious axe violations', async () => {
    const { container } = render(
      <MemoryRouter>
        <Result />
      </MemoryRouter>,
    )
    const results = await axe(container)
    const serious = results.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious')
    expect(serious).toEqual([])
  })
})
