import { useMutation } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import type { Debrief as DebriefData } from '../api/types.ts'
import { api } from '../api/client.ts'
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

export function Debrief() {
  const { sessionId = '' } = useParams()
  const [debrief, setDebrief] = useState<DebriefData | null>(() => loadDebrief(sessionId))
  const requested = useRef(false)

  const fetchDebrief = useMutation({
    mutationFn: () => {
      const hungUp = sessionStorage.getItem(`debrief_hungup_${sessionId}`) === '1'
      return api.finishDrill(sessionId, hungUp)
    },
    onSuccess: (data) => {
      sessionStorage.setItem(`debrief_${sessionId}`, JSON.stringify(data))
      setDebrief(data)
    },
  })

  useEffect(() => {
    if (debrief || requested.current) return
    if (sessionStorage.getItem(`debrief_pending_${sessionId}`)) {
      requested.current = true
      sessionStorage.removeItem(`debrief_pending_${sessionId}`)
      fetchDebrief.mutate()
    }
  }, [debrief, sessionId, fetchDebrief])

  const remind = () => {
    const when = Date.now() + 7 * 24 * 60 * 60 * 1000
    localStorage.setItem('scam_shield_practise_reminder', String(when))
  }

  if (!debrief && fetchDebrief.isPending) return <p>{strings.loading}</p>
  if (!debrief) {
    return (
      <div className="page-column">
        <p>{strings.genericError}</p>
        <Link className="btn btn--secondary" to="/practise">
          {strings.debriefAgain}
        </Link>
      </div>
    )
  }

  return (
    <div className="page-column">
      <h1>{strings.debriefTitle}</h1>
      <section>
        <h2>{strings.debriefTimeline}</h2>
        <p>{debrief.summary_plain}</p>
        {debrief.moments.length > 0 ? (
          <ol>
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
      <section>
        <h2>{strings.debriefWell}</h2>
        <ul>
          {debrief.what_you_did_well.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      </section>
      <section>
        <h2>{strings.debriefNext}</h2>
        <p>{debrief.one_thing_to_try}</p>
      </section>
      <div className="stack">
        <Link className="btn btn--primary btn--block" to="/practise">
          {strings.debriefAgain}
        </Link>
        <button type="button" className="btn btn--secondary btn--block" onClick={remind}>
          {strings.debriefRemind}
        </button>
      </div>
    </div>
  )
}
