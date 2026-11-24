import { useEffect, useRef } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { clearApiError } from '../api/client.ts'
import { Header } from './Header.tsx'
import { LocalBannerHost, MessageBanner } from './MessageBanner.tsx'
import { PracticeBanner } from './PracticeBanner.tsx'
import { SkipLink } from './SkipLink.tsx'

const PAGE_TITLES: [RegExp, string][] = [
  [/^\/$/, 'Home'],
  [/^\/check\/result/, 'What we found'],
  [/^\/check/, 'Check a message'],
  [/^\/practise\/chat/, 'Practice chat'],
  [/^\/practise\/debrief/, 'How you did'],
  [/^\/practise/, 'Practise'],
  [/^\/help/, 'Help now'],
  [/^\/family/, 'My family'],
  [/^\/scams-near-me/, 'Scams near me'],
  [/^\/settings/, 'Text size and contrast'],
  [/^\/invite/, 'Family invitation'],
]

function titleFor(pathname: string): string {
  const match = PAGE_TITLES.find(([re]) => re.test(pathname))
  return match ? `${match[1]} · Scam Shield` : 'Scam Shield'
}

export function Layout() {
  const { pathname } = useLocation()
  const mainRef = useRef<HTMLElement | null>(null)
  const firstRender = useRef(true)

  // On every page change: clear old errors, start at the top, and move focus
  // to the new page heading so screen readers announce where the user is.
  useEffect(() => {
    clearApiError()
    window.dispatchEvent(new CustomEvent('scam-shield-banner', { detail: null }))
    document.title = titleFor(pathname)
    if (firstRender.current) {
      firstRender.current = false
      return
    }
    window.scrollTo(0, 0)
    const frame = window.requestAnimationFrame(() => {
      const main = mainRef.current
      if (!main) return
      const heading = main.querySelector<HTMLElement>('h1')
      const target = heading ?? main
      if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1')
      target.focus({ preventScroll: true })
    })
    return () => window.cancelAnimationFrame(frame)
  }, [pathname])
  const showPractice =
    pathname.startsWith('/practise/chat') || pathname.startsWith('/practise/debrief')

  return (
    <div className="app-shell">
      <SkipLink />
      <Header />
      {showPractice ? <PracticeBanner /> : null}
      <MessageBanner />
      <LocalBannerHost />
      <main id="main-content" className="app-main" ref={mainRef} tabIndex={-1}>
        <Outlet />
      </main>
      <footer className="app-footer">
        <div className="app-footer__inner">
          Scam Shield is a guide, not a guarantee. If unsure, use a number you already know.
        </div>
      </footer>
    </div>
  )
}
