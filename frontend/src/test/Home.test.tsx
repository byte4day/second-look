import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { axe } from 'vitest-axe'
import { Home } from '../pages/Home.tsx'

describe('Home', () => {
  it('renders Bit, heading, and numbered choices', () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>,
    )
    expect(screen.getByText(/i'm bit/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /is something worrying you/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /check a message/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /i need help now/i })).toBeInTheDocument()
    const links = screen.getAllByRole('link')
    expect(links.map((l) => l.textContent?.charAt(0))).toEqual(['1', '2', '3', '4', '5'])
  })

  it('has no axe violations', async () => {
    const { container } = render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>,
    )
    const results = await axe(container)
    expect(results.violations).toEqual([])
  })
})
