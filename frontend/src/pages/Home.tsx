import { Link } from 'react-router-dom'
import { strings } from '../strings.ts'

const linkClass = 'btn btn--secondary btn--block'

export function Home() {
  return (
    <div className="page-column">
      <h1>{strings.homeTitle}</h1>
      <nav className="stack" aria-label="Main choices">
        <Link className={linkClass} to="/check">
          {strings.homeCheck}
        </Link>
        <Link className={linkClass} to="/practise">
          {strings.homePractise}
        </Link>
        <Link className={linkClass} to="/family">
          {strings.homeFamily}
        </Link>
        <Link className={linkClass} to="/scams-near-me">
          {strings.homeScamsNear}
        </Link>
      </nav>
      <p className="note">{strings.homeNote}</p>
    </div>
  )
}
