import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, TextInput } from '../components/FormField.tsx'
import { useToken } from '../hooks/useToken.ts'
import { smsLink, whatsAppLink } from '../lib/shareLinks.ts'
import { strings } from '../strings.ts'

const TEST_SENT = 'Test alert sent. Your accepted contacts should get an email soon.'

export function Family() {
  const token = useToken()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [formError, setFormError] = useState<string | undefined>()

  const contacts = useQuery({
    queryKey: ['family'],
    queryFn: () => api.listFamily(),
    enabled: Boolean(token),
  })

  const addContact = useMutation({
    mutationFn: () => api.addFamily(name.trim(), email.trim()),
    onSuccess: () => {
      setName('')
      setEmail('')
      setFormError(undefined)
      void queryClient.invalidateQueries({ queryKey: ['family'] })
    },
    onError: (err: Error) => setFormError(err.message),
  })

  const testAlert = useMutation({
    mutationFn: () => api.sendTestAlert(),
  })

  return (
    <div className="page-column">
      <h1>{strings.familyTitle}</h1>
      <p className="page-lead">{strings.familyIntro}</p>

      <div className="family-fallback">
        <h2>{strings.familyShareNow}</h2>
        <p className="note">{strings.familyShareHint}</p>
        <a className="btn btn--primary btn--block" href={smsLink(strings.familyShareBody)}>
          {strings.familyShareSms}
        </a>
        <a
          className="btn btn--secondary btn--block"
          href={whatsAppLink(strings.familyShareBody)}
          target="_blank"
          rel="noopener noreferrer"
        >
          {strings.familyShareWhatsApp}
        </a>
      </div>

      {!token ? <p className="note">{strings.familySignInNote}</p> : null}
      {token && contacts.isLoading ? <p>{strings.loading}</p> : null}
      {token && contacts.data ? (
        <ul className="contact-list">
          {contacts.data.map((c) => (
            <li key={c.id}>
              <div>
                <strong>{c.name}</strong> — {c.email}
                <br />
                <span
                  className={
                    c.status === 'accepted'
                      ? 'status-pill status-pill--accepted'
                      : 'status-pill status-pill--waiting'
                  }
                >
                  {c.status === 'accepted'
                    ? strings.familyStatusAccepted
                    : strings.familyStatusWaiting}
                </span>
              </div>
              <Link className="btn btn--secondary" to={`/family/remove/${c.id}`}>
                {strings.familyRemove}
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
      {token ? (
        <>
          <FormField id="fname" label={strings.familyName} error={formError}>
            <TextInput
              id="fname"
              value={name}
              maxLength={120}
              autoComplete="name"
              onChange={(e) => setName(e.target.value)}
            />
          </FormField>
          <FormField id="femail" label={strings.familyEmail}>
            <TextInput
              id="femail"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </FormField>
          <Button
            variant="primary"
            block
            disabled={!name.trim() || !email.trim() || addContact.isPending}
            onClick={() => addContact.mutate()}
          >
            {strings.familyAdd}
          </Button>
          <Button
            variant="secondary"
            block
            disabled={testAlert.isPending}
            onClick={() => testAlert.mutate()}
          >
            {strings.familyTest}
          </Button>
          {testAlert.isSuccess ? (
            <p className="note" role="status">
              {TEST_SENT}
            </p>
          ) : null}
          {testAlert.isError ? (
            <p className="note" role="alert">
              {testAlert.error.message}
            </p>
          ) : null}
        </>
      ) : (
        <Link className="btn btn--secondary btn--block" to="/settings">
          {strings.settingsSignIn}
        </Link>
      )}
    </div>
  )
}
