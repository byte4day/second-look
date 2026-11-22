import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { axe } from 'vitest-axe'
import { Home } from '../pages/Home.tsx'

describe('Home', () => {
  it('renders main heading and choices', () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: /is something worrying you/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /check a message/i })).toBeInTheDocument()
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