import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { useSpeech } from '../hooks/useSpeech.ts'
import { smsLink, whatsAppLink } from '../lib/shareLinks.ts'
import { strings } from '../strings.ts'

export function HelpNow() {
  const { available, speak } = useSpeech()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['help-now'],
    queryFn: () => api.helpNow(),
  })

  const steps = data?.help_now_steps ?? [
    'Stop talking to the person.',
    'Do not pay or share codes or passwords.',
    'Hang up or close the chat.',
    'Call your bank using the number printed on your card.',
    'Tell someone you trust.',
  ]

  const bodyForShare = steps.join(' ').slice(0, 300)

  const readPage = () => {
    const contactLines =
      data?.who_to_contact.map((c) => `${c.name}. ${c.how}`) ?? []
    speak([strings.helpTitle, ...steps, ...contactLines].join('. '))
  }

  return (
    <div className="page-column">
      <h1>{strings.helpTitle}</h1>
      {isLoading ? <p>{strings.loading}</p> : null}
      {isError ? <p role="alert">{strings.offlineHelp}</p> : null}
      <ol className="numbered-steps">
        {steps.map((step, i) => (
          <li key={i}>{step}</li>
        ))}
      </ol>
      <section className="stack">
        <h2>{strings.helpWhoToContact}</h2>
        {data?.who_to_contact.map((entry, i) => (
          <div key={i}>
            <p>
              <strong>{entry.name}</strong>
            </p>
            <p>{entry.how}</p>
          </div>
        ))}
        <Link className="btn btn--danger btn--block" to="/family">
          {strings.helpTellFamily}
        </Link>
        {available ? (
          <Button variant="secondary" block onClick={readPage}>
            {strings.helpReadAloud}
          </Button>
        ) : null}
        <a className="btn btn--secondary btn--block" href={smsLink(bodyForShare)}>
          Send steps by text message
        </a>
        <a
          className="btn btn--secondary btn--block"
          href={whatsAppLink(bodyForShare)}
          target="_blank"
          rel="noopener noreferrer"
        >
          Send steps by WhatsApp
        </a>
      </section>
    </div>
  )
}
