import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE } from '../api/client.ts'
import { useSpeech } from './useSpeech.ts'

export type CallerPersona = 'caller' | 'victim'

/**
 * Plays scammer / victim lines as real audio from the API (Orpheus or phone-style).
 * Falls back to browser speechSynthesis only if the API fails.
 *
 * Each play() gets a call id. stop(), a newer play() or unmount makes older calls
 * stale: their fetch is aborted and they never start audio or fall back to speech.
 */
export function useCallerVoice() {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const objectUrlRef = useRef<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const callIdRef = useRef(0)
  const settleRef = useRef<(() => void) | null>(null)
  const [busy, setBusy] = useState(false)
  const [lastEngine, setLastEngine] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { available: browserOk, speak: browserSpeak, stop: browserStop } = useSpeech()

  const release = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    const audio = audioRef.current
    if (audio) {
      audio.onended = null
      audio.onerror = null
      audio.pause()
      audio.removeAttribute('src')
      audio.load()
      audioRef.current = null
    }
    // Let a pending play() promise finish instead of hanging forever.
    settleRef.current?.()
    settleRef.current = null
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current)
      objectUrlRef.current = null
    }
  }, [])

  const stop = useCallback(() => {
    callIdRef.current += 1
    release()
    browserStop()
    setBusy(false)
  }, [browserStop, release])

  useEffect(() => () => stop(), [stop])

  const play = useCallback(
    async (text: string, persona: CallerPersona = 'caller') => {
      stop()
      const callId = callIdRef.current
      const isCurrent = () => callIdRef.current === callId
      const controller = new AbortController()
      abortRef.current = controller
      setError(null)
      setBusy(true)
      try {
        const res = await fetch(`${API_BASE}/api/voice/speak`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, persona }),
          signal: controller.signal,
        })
        if (!isCurrent()) return
        if (!res.ok) throw new Error('tts_http')
        setLastEngine(res.headers.get('X-Scam-Shield-TTS-Engine'))
        const blob = await res.blob()
        if (!isCurrent()) return
        const url = URL.createObjectURL(blob)
        objectUrlRef.current = url
        const audio = new Audio(url)
        audioRef.current = audio
        await new Promise<void>((resolve, reject) => {
          settleRef.current = resolve
          audio.onended = () => resolve()
          audio.onerror = () => reject(new Error('audio_play'))
          void audio.play().catch(reject)
        })
      } catch {
        // A stopped or replaced call exits quietly. Only a real failure falls back.
        if (!isCurrent()) return
        if (browserOk) {
          setLastEngine('browser')
          browserSpeak(text, persona === 'victim' ? 'victim' : 'caller')
        } else {
          setError('Caller voice could not play on this device.')
        }
      } finally {
        if (isCurrent()) {
          abortRef.current = null
          setBusy(false)
        }
      }
    },
    [browserOk, browserSpeak, stop],
  )

  return { play, stop, busy, lastEngine, error, ready: true }
}
