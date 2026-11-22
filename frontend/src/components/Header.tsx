import { Link, useLocation } from 'react-router-dom'
import { strings } from '../strings.ts'

const primary = 'btn btn--danger'
const secondary = 'btn btn--secondary'

export function Header() {
  const { pathname } = useLocation()
  const onHome = pathname === '/'

  return (
    <header className="site-header">
      <Link to="/" className="site-header__brand">
        {strings.appName}
      </Link>
      <div className="site-header__actions">
        <Link to="/help" className={primary}>
          {strings.helpNow}
        </Link>
        <Link to="/settings" className={secondary}>
          {strings.textSizeContrast}
        </Link>
        {!onHome ? (
          <Link to="/" className={secondary}>
            {strings.backToStart}
          </Link>
        ) : null}
      </div>
    </header>
  )
}