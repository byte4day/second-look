import { Link } from 'react-router-dom'
import { BitSays } from '../components/Bit.tsx'
import { strings } from '../strings.ts'

type Choice = { to: string; label: string; hint: string; className: string }

const primaryChoices: Choice[] = [
  {
    to: '/check',
    label: strings.homeCheck,
    hint: strings.homeCheckHint,
    className: 'btn btn--primary btn--block btn--numbered',
  },
  {
    to: '/practise',
    label: strings.homePractise,
    hint: strings.homePractiseHint,
    className: 'btn btn--secondary btn--block btn--numbered',
  },
]

const secondaryChoices: Choice[] = [
  {
    to: '/help',
    label: strings.helpNow,
    hint: strings.homeHelpHint,
    className: 'btn btn--danger btn--block btn--numbered',
  },
  {
    to: '/family',
    label: strings.homeFamily,
    hint: strings.homeFamilyHint,
    className: 'btn btn--secondary btn--block btn--numbered',
  },
  {
    to: '/scams-near-me',
    label: strings.homeScamsNear,
    hint: strings.homeScamsHint,
    className: 'btn btn--secondary btn--block btn--numbered',
  },
]

function ChoiceLink({ choice, n }: { choice: Choice; n: number }) {
  return (
    <div className="home-choice">
      <Link className={choice.className} to={choice.to}>
        <span className="num-tag" aria-hidden="true">
          {n}
        </span>
        <span>{choice.label}</span>
      </Link>
      <p className="home-choice__hint">{choice.hint}</p>
    </div>
  )
}

export function Home() {
  return (
    <div className="page-column">
      <div className="home-hero">
        <h1>{strings.homeTitle}</h1>
        <p className="page-lead">{strings.homeLead}</p>
        <BitSays mood="happy" size={96}>
          <p>{strings.bitHello}</p>
          <p>{strings.bitHelloTip}</p>
        </BitSays>
      </div>

      <nav className="stack" aria-label="Main choices">
        {primaryChoices.map((choice, i) => (
          <ChoiceLink key={choice.to} choice={choice} n={i + 1} />
        ))}
      </nav>

      <div className="home-split">
        <nav className="stack" aria-label="More help">
          {secondaryChoices.map((choice, i) => (
            <ChoiceLink key={choice.to} choice={choice} n={i + 1 + primaryChoices.length} />
          ))}
        </nav>
      </div>

      <p className="note">{strings.homePromise} {strings.homeNote}</p>
    </div>
  )
}
