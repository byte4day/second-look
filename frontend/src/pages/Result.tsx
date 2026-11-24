import { Link, Navigate } from 'react-router-dom'
import type { RiskLevel } from '../api/types.ts'
import { HighlightedText, ReasonLegend } from '../components/HighlightedText.tsx'
import { Button } from '../components/Button.tsx'
import { BitSays, type BitMood } from '../components/Bit.tsx'
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

const bitMood: Record<RiskLevel, BitMood> = {
  likely_scam: 'worried',
  suspicious: 'worried',
  probably_ok: 'happy',
  cannot_tell: 'thinking',
}

const bitLine: Record<RiskLevel, string> = {
  likely_scam: strings.bitLikely,
  suspicious: strings.bitSuspicious,
  probably_ok: strings.bitOk,
  cannot_tell: strings.bitUnknown,
}

export function Result() {
  const data = loadCheckResult()
  const { available, speak } = useSpeech()
  if (!data) return <Navigate to="/check" replace />

  const { result, source } = data
  const quotes = result.reasons.map((r) => r.quote)
  // Sections show in a fixed order; number only the ones that render.
  const sectionKeys = [
    quotes.length > 0 && 'flags',
    quotes.length === 0 && result.reasons.length > 0 && 'why',
    result.what_to_do_now.length > 0 && 'do',
    result.what_not_to_do.length > 0 && 'dont',
  ].filter(Boolean) as string[]
  const numbered = (key: string, title: string) => (
    <h2 className="step-heading">
      <span className="num-tag" aria-hidden="true">
        {sectionKeys.indexOf(key) + 1}
      </span>
      <span>{title}</span>
    </h2>
  )

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
      <p className="note">{strings.resultTitle}</p>
      <h1>{result.headline}</h1>
      <div className={riskClass[result.risk_level]} role="status">
        <p className="risk-box__label">{strings.resultRisk}</p>
        <div className="risk-box__value">{riskLabel[result.risk_level]}</div>
      </div>
      <BitSays mood={bitMood[result.risk_level]} size={80}>
        <p>{bitLine[result.risk_level]}</p>
      </BitSays>
      {quotes.length > 0 ? (
        <section className="page-section">
          {numbered('flags', strings.resultFlags)}
          <div className="message-source">
            <HighlightedText text={source} quotes={quotes} />
          </div>
          <ReasonLegend reasons={result.reasons} />
        </section>
      ) : null}
      {quotes.length === 0 && result.reasons.length > 0 ? (
        <section className="page-section">
          {numbered('why', strings.resultWhy)}
          <ol>
            {result.reasons.map((r, i) => (
              <li key={i}>{r.why}</li>
            ))}
          </ol>
        </section>
      ) : null}
      {result.what_to_do_now.length > 0 ? (
        <section className="page-section">
          {numbered('do', strings.resultDo)}
          <ol className="numbered-steps">
            {result.what_to_do_now.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </section>
      ) : null}
      {result.what_not_to_do.length > 0 ? (
        <section className="page-section">
          {numbered('dont', strings.resultDoNot)}
          <ul className="red-flag-list">
            {result.what_not_to_do.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        </section>
      ) : null}
      <p className="note">{result.note}</p>
      <div className="sticky-actions">
        {available ? (
          <Button variant="secondary" block onClick={readAloud}>
            {strings.resultReadAloud}
          </Button>
        ) : null}
        <Link className="btn btn--danger btn--block" to="/help">
          {strings.helpNow}
        </Link>
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
