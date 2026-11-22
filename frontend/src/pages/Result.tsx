import { Link } from 'react-router-dom'
import { Navigate } from 'react-router-dom'
import type { RiskLevel } from '../api/types.ts'
import { HighlightedText, ReasonLegend } from '../components/HighlightedText.tsx'
import { Button } from '../components/Button.tsx'
import { useSpeech } from '../hooks/useSpeech.ts'
import { strings } from '../strings.ts'
import { loadCheckResult } from './CheckMessage.tsx'

const riskClass: Record<RiskLevel, string> = {
  likely_scam: 'risk-box risk-box--likely',
  suspicious: 'risk-box risk-box--suspicious',
  probably_ok: 'risk-box risk-box--ok',
  cannot_tell: 'risk-box risk-box--unknown',
}

const riskLabel: Record<RiskLevel, string> = {
  likely_scam: strings.riskLikely,
  suspicious: strings.riskSuspicious,
  probably_ok: strings.riskOk,
  cannot_tell: strings.riskUnknown,
}

export function Result() {
  const data = loadCheckResult()
  const { available, speak } = useSpeech()
  if (!data) return <Navigate to="/check" replace />

  const { result, source } = data
  const quotes = result.reasons.map((r) => r.quote)

  const readAloud = () => {
    const text = [
      result.headline,
      riskLabel[result.risk_level],
      ...result.reasons.map((r) => r.why),
      ...result.what_to_do_now,
      ...result.what_not_to_do,
      result.note,
    ].join('. ')
    speak(text)
  }

  return (
    <div className="page-column">
      <h1>{result.headline}</h1>
      <div className={riskClass[result.risk_level]} role="status">
        <strong>{strings.resultRisk}: </strong>
        {riskLabel[result.risk_level]}
      </div>
      {quotes.length > 0 ? (
        <section>
          <h2>{strings.resultFlags}</h2>
          <HighlightedText text={source} quotes={quotes} />
          <ReasonLegend reasons={result.reasons} />
        </section>
      ) : null}
      {result.reasons.length > 0 ? (
        <section>
          <h2>{strings.resultWhy}</h2>
          <ol>
            {result.reasons.map((r, i) => (
              <li key={i}>{r.why}</li>
            ))}
          </ol>
        </section>
      ) : null}
      {result.what_to_do_now.length > 0 ? (
        <section>
          <h2>{strings.resultDo}</h2>
          <ol>
            {result.what_to_do_now.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </section>
      ) : null}
      {result.what_not_to_do.length > 0 ? (
        <section>
          <h2>{strings.resultDoNot}</h2>
          <ul>
            {result.what_not_to_do.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        </section>
      ) : null}
      <p className="note">{result.note}</p>
      <div className="stack">
        {available ? (
          <Button variant="secondary" block onClick={readAloud}>
            {strings.resultReadAloud}
          </Button>
        ) : null}
        <Link className="btn btn--secondary btn--block" to="/family">
          {strings.resultTellFamily}
        </Link>
        <Link className="btn btn--secondary btn--block" to="/scams-near-me">
          {strings.resultReport}
        </Link>
        <Link className="btn btn--primary btn--block" to="/check">
          {strings.resultCheckAnother}
        </Link>
      </div>
    </div>
  )
}
