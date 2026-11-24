import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api, setToken } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, TextInput } from '../components/FormField.tsx'
import {
  type ContrastMode,
  type TextSize,
  usePreferences,
} from '../hooks/usePreferences.ts'
import { useToken } from '../hooks/useToken.ts'
import { strings } from '../strings.ts'

const CODE_SENT = 'We sent a six-digit code to your email. It may take a minute to arrive.'
const DELETE_START = 'Delete my account and data'
const DELETE_CHECK = 'Are you sure? This cannot be undone.'
const KEEP_DATA = 'No, keep my account'
const DELETE_YES = 'Yes, delete my account and data'

export function Settings() {
  const { textSize, contrast, setTextSize, setContrast } = usePreferences()
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [authError, setAuthError] = useState<string | undefined>()
  const [confirmDelete, setConfirmDelete] = useState(false)
  const queryClient = useQueryClient()
  const signedIn = Boolean(useToken())

  const me = useQuery({
    queryKey: ['me'],
    queryFn: () => api.me(),
    enabled: signedIn,
  })

  const requestCode = useMutation({
    mutationFn: () => api.requestCode(email.trim()),
    onSuccess: () => setAuthError(undefined),
    onError: (err: Error) => setAuthError(err.message),
  })

  const verify = useMutation({
    mutationFn: () => api.verifyCode(email.trim(), code.trim()),
    onSuccess: (data) => {
      setToken(data.access_token)
      setAuthError(undefined)
      void queryClient.invalidateQueries({ queryKey: ['me'] })
    },
    onError: (err: Error) => setAuthError(err.message),
  })

  const deleteData = useMutation({
    mutationFn: () => api.deleteMe(),
    onSuccess: () => {
      setConfirmDelete(false)
      setToken(null)
      queryClient.clear()
    },
  })

  const signOut = () => {
    setToken(null)
    setConfirmDelete(false)
    queryClient.clear()
  }

  return (
    <div className="page-column">
      <h1>{strings.settingsTitle}</h1>
      <fieldset className="radio-group">
        <legend>{strings.settingsTextSize}</legend>
        {(
          [
            ['normal', strings.settingsSizeNormal],
            ['large', strings.settingsSizeLarge],
            ['extra-large', strings.settingsSizeExtraLarge],
          ] as const
        ).map(([value, label]) => (
          <label key={value} className="radio-option">
            <input
              type="radio"
              name="text-size"
              checked={textSize === value}
              onChange={() => setTextSize(value as TextSize)}
            />
            {label}
          </label>
        ))}
      </fieldset>
      <fieldset className="radio-group">
        <legend>{strings.settingsContrast}</legend>
        {(
          [
            ['standard', strings.settingsContrastStandard],
            ['high', strings.settingsContrastHigh],
          ] as const
        ).map(([value, label]) => (
          <label key={value} className="radio-option">
            <input
              type="radio"
              name="contrast"
              checked={contrast === value}
              onChange={() => setContrast(value as ContrastMode)}
            />
            {label}
          </label>
        ))}
      </fieldset>
      <section>
        <h2>{strings.settingsSignIn}</h2>
        {signedIn && me.data ? (
          <>
            <p>
              {strings.settingsSignedIn} {me.data.email}
            </p>
            <Button variant="secondary" onClick={signOut}>
              {strings.settingsSignOut}
            </Button>
          </>
        ) : (
          <>
            <FormField id="email" label={strings.settingsEmail} error={authError}>
              <TextInput id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </FormField>
            <Button
              variant="secondary"
              disabled={!email.trim() || requestCode.isPending}
              onClick={() => requestCode.mutate()}
            >
              {strings.settingsRequestCode}
            </Button>
            {requestCode.isSuccess ? (
              <p className="note" role="status">
                {CODE_SENT}
              </p>
            ) : null}
            <FormField id="code" label={strings.settingsCode}>
              <TextInput id="code" inputMode="numeric" value={code} onChange={(e) => setCode(e.target.value)} />
            </FormField>
            <Button
              variant="primary"
              block
              disabled={code.length < 6 || verify.isPending}
              onClick={() => verify.mutate()}
            >
              {strings.settingsVerify}
            </Button>
          </>
        )}
      </section>
      {signedIn ? (
        <section>
          {confirmDelete ? (
            <div className="panel stack" role="group" aria-label={DELETE_CHECK}>
              <p>{strings.settingsDeleteConfirm}</p>
              <p>
                <strong>{DELETE_CHECK}</strong>
              </p>
              <Button
                variant="danger"
                block
                disabled={deleteData.isPending}
                onClick={() => deleteData.mutate()}
              >
                {DELETE_YES}
              </Button>
              <Button variant="secondary" block onClick={() => setConfirmDelete(false)}>
                {KEEP_DATA}
              </Button>
            </div>
          ) : (
            <Button variant="secondary" block onClick={() => setConfirmDelete(true)}>
              {DELETE_START}
            </Button>
          )}
          {deleteData.isError ? (
            <p className="note" role="alert">
              {deleteData.error.message}
            </p>
          ) : null}
        </section>
      ) : null}
    </div>
  )
}