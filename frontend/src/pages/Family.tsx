import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getToken } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, TextInput } from '../components/FormField.tsx'
import { strings } from '../strings.ts'

export function Family() {
  const token = getToken()
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
      <p>{strings.familyIntro}</p>
      {!token ? <p className="note">{strings.familySignInNote}</p> : null}
      {token && contacts.isLoading ? <p>{strings.loading}</p> : null}
      {token && contacts.data ? (
        <ul className="contact-list">
          {contacts.data.map((c) => (
            <li key={c.id}>
              <div>
                <strong>{c.name}</strong> — {c.email}
                <br />
                <span className="note">
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
            <TextInput id="fname" value={name} onChange={(e) => setName(e.target.value)} />
          </FormField>
          <FormField id="femail" label={strings.familyEmail}>
            <TextInput
              id="femail"
              type="email"
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
        </>
      ) : (
        <Link className="btn btn--primary btn--block" to="/settings">
          {strings.settingsSignIn}
        </Link>
      )}
    </div>
  )
}