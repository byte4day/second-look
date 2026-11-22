import { Outlet, useLocation } from 'react-router-dom'
import { Header } from './Header.tsx'
import { LocalBannerHost, MessageBanner } from './MessageBanner.tsx'
import { PracticeBanner } from './PracticeBanner.tsx'
import { SkipLink } from './SkipLink.tsx'

export function Layout() {
  const { pathname } = useLocation()
  const showPractice =
    pathname.startsWith('/practise/chat') || pathname.startsWith('/practise/debrief')

  return (
    <div className="app-shell">
      <SkipLink />
      <Header />
      {showPractice ? <PracticeBanner /> : null}
      <MessageBanner />
      <LocalBannerHost />
      <main id="main-content" className="app-main">
        <Outlet />
      </main>
    </div>
  )
}