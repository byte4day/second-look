import { useMutation } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import type { Debrief as DebriefData } from '../api/types.ts'
import { api } from '../api/client.ts'
import { BitSays } from '../components/Bit.tsx'
import { strings } from '../strings.ts'

function loadDebrief(sessionId: string): DebriefData | null {
  const raw = sessionStorage.getItem(`debrief_${sessionId}`)
  if (!raw) return null
  try {
    return JSON.parse(raw) as DebriefData
  } catch {
    return null
  }
}

const DEBRIEF_FAILED =
  'We could not load your summary just now. Your practice still counts. Try again in a moment.'
const TRY_AGAIN = 'Try again'

export function Debrief() {
  const { sessionId = '' } = useParams()
  const [debrief, setDebrief] = useState<DebriefData | null>(() => loadDebrief(sessionId))
  const [reminded, setReminded] = useState(false)
  const requested = useRef(false)

  const fetchDebrief = useMutation({
    mutationFn: () => {
      const hungUp = sessionStorage.getItem(`debrief_hungup_${sessionId}`) === '1'
      return api.finishDrill(sessionId, hungUp)
    },
    onSuccess: (data) => {
      sessionStorage.setItem(`debrief_${sessionId}`, JSON.stringify(data))
      sessionStorage.removeItem(`debrief_pending_${sessionId}`)
      setDebrief(data)
    },
  })

  useEffect(() => {
    if (debrief || requested.current) return
    if (sessionStorage.getItem(`debrief_pending_${sessionId}`)) {
      requested.current = true
      fetchDebrief.mutate()
    }
  }, [debrief, sessionId, fetchDebrief])

  const remind = () => {
    const when = Date.now() + 7 * 24 * 60 * 60 * 1000
    localStorage.setItem('scam_shield_practise_reminder', String(when))
    setReminded(true)
  }

  if (!debrief && fetchDebrief.isPending) {
    return (
      <div className="page-column">
        <h1>{strings.debriefTitle}</h1>
        <p role="status">{strings.loading}</p>
      </div>
    )
  }
  if (!debrief) {
    return (
      <div className="page-column">
        <h1>{strings.debriefTitle}</h1>
        <p role="alert">{DEBRIEF_FAILED}</p>
        <button
          type="button"
          className="btn btn--primary btn--block"
          onClick={() => fetchDebrief.mutate()}
        >
          {TRY_AGAIN}
        </button>
        <Link className="btn btn--secondary btn--block" to="/practise">
          {strings.debriefAgain}
        </Link>
      </div>
    )
  }

  return (
    <div className="page-column">
      <h1>{strings.debriefTitle}</h1>
      <BitSays mood="happy" size={72}>
        <p>Well done for practising. Every trick you spot here is one a real scammer cannot use on you.</p>
      </BitSays>
      <div className="debrief-praise" role="status">
        <p>
          <strong>{strings.debriefWell}</strong>
        </p>
        <ul>
          {debrief.what_you_did_well.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      </div>
      <section className="page-section">
        <h2>{strings.debriefTimeline}</h2>
        <p>{debrief.summary_plain}</p>
        {debrief.moments.length > 0 ? (
          <ol className="timeline">
            {debrief.moments.map((m, i) => (
              <li key={i}>
                <mark className="highlight-mark">{m.quote}</mark>
                {' — '}
                {m.why}
              </li>
            ))}
          </ol>
        ) : null}
      </section>
      <section className="page-section">
        <h2>{strings.debriefNext}</h2>
        <p>{debrief.one_thing_to_try}</p>
      </section>
      <div className="sticky-actions">
        <Link className="btn btn--primary btn--block" to="/practise">
          {strings.debriefAgain}
        </Link>
        <button type="button" className="btn btn--secondary btn--block" onClick={remind}>
          {reminded ? strings.debriefRemindDone : strings.debriefRemind}
        </button>
        <Link className="btn btn--secondary btn--block" to="/">
          {strings.resultHome}
        </Link>
      </div>
    </div>
  )
}
