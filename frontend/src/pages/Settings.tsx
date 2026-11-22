import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api, getToken, setToken } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, TextInput } from '../components/FormField.tsx'
import {
  type ContrastMode,
  type TextSize,
  usePreferences,
} from '../hooks/usePreferences.ts'
import { strings } from '../strings.ts'

export function Settings() {
  const {
    textSize,
    contrast,
    readAloud,
    setTextSize,
    setContrast,
    setReadAloud,
  } = usePreferences()
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [authError, setAuthError] = useState<string | undefined>()
  const queryClient = useQueryClient()
  const signedIn = Boolean(getToken())

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
      setToken(null)
      void queryClient.clear()
    },
  })

  const signOut = () => {
    setToken(null)
    void queryClient.clear()
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
      <label className="radio-option">
        <input
          type="checkbox"
          checked={readAloud}
          onChange={(e) => setReadAloud(e.target.checked)}
        />
        {strings.settingsReadAloud}
      </label>
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
          <p>{strings.settingsDeleteConfirm}</p>
          <Button variant="danger" block disabled={deleteData.isPending} onClick={() => deleteData.mutate()}>
            {strings.settingsDeleteYes}
          </Button>
        </section>
      ) : null}
    </div>
  )
}