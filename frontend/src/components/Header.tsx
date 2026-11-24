import { Link, useLocation } from 'react-router-dom'
import { strings } from '../strings.ts'
import { Bit } from './Bit.tsx'

export function Header() {
  const { pathname } = useLocation()
  const onHome = pathname === '/'

  return (
    <header className="site-header">
      <div className="site-header__row">
        <Link to="/" className="site-header__brand">
          <Bit mood="calm" size={34} className="site-header__bit" />
          <span>{strings.appName}</span>
        </Link>
        <div className="site-header__actions">
          <Link to="/help" className="btn btn--danger">
            {strings.helpNow}
          </Link>
          <Link to="/settings" className="btn btn--secondary">
            {strings.textSizeContrast}
          </Link>
        </div>
      </div>
      {!onHome ? (
        <div className="site-header__back">
          <Link to="/">{strings.backToStart}</Link>
        </div>
      ) : null}
    </header>
  )
}
