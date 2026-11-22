import { useEffect, useState } from 'react'
import { setApiErrorListener } from '../api/client.ts'
import { strings } from '../strings.ts'
import { Button } from './Button.tsx'

export function MessageBanner() {
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    setApiErrorListener(setMessage)
    return () => setApiErrorListener(() => undefined)
  }, [])

  if (!message) return null

  return (
    <div className="error-banner" role="alert">
      <p>
        {strings.problemPrefix}
        {message}
      </p>
      <Button variant="secondary" onClick={() => setMessage(null)}>
        {strings.close}
      </Button>
    </div>
  )
}

export function LocalBannerHost() {
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<string>).detail
      setMessage(detail)
    }
    window.addEventListener('scam-shield-banner', handler)
    return () => window.removeEventListener('scam-shield-banner', handler)
  }, [])

  if (!message) return null

  return (
    <div className="error-banner" role="alert">
      <p>
        {strings.problemPrefix}
        {message}
      </p>
      <Button variant="secondary" onClick={() => setMessage(null)}>
        {strings.close}
      </Button>
    </div>
  )
}