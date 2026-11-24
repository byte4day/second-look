import { useCallback, useEffect, useState } from 'react'

export type SpeechRole = 'default' | 'caller' | 'victim'

function pickVoice(role: SpeechRole): SpeechSynthesisVoice | null {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null
  const voices = window.speechSynthesis.getVoices()
  if (!voices.length) return null

  const english = voices.filter((v) => v.lang.toLowerCase().startsWith('en'))
  const pool = english.length ? english : voices

  if (role === 'caller') {
    // Prefer a lower, more "phone call" sounding English voice when available.
    const preferred =
      pool.find((v) => /daniel|david|alex|fred|male|uk english male/i.test(v.name)) ||
      pool.find((v) => /en-gb|en_gb/i.test(v.lang)) ||
      pool[0]
    return preferred
  }

  if (role === 'victim') {
    const preferred =
      pool.find((v) => /samantha|karen|moira|female|uk english female/i.test(v.name)) ||
      pool.find((v) => /en-gb|en_gb/i.test(v.lang)) ||
      pool[Math.min(1, pool.length - 1)]
    return preferred
  }

  return pool.find((v) => /en-gb|en_gb/i.test(v.lang)) || pool[0]
}

export function useSpeech() {
  const available = typeof window !== 'undefined' && 'speechSynthesis' in window
  const [voicesReady, setVoicesReady] = useState(false)

  useEffect(() => {
    if (!available) return
    const sync = () => setVoicesReady(window.speechSynthesis.getVoices().length > 0)
    sync()
    window.speechSynthesis.addEventListener('voiceschanged', sync)
    return () => window.speechSynthesis.removeEventListener('voiceschanged', sync)
  }, [available])

  const speak = useCallback(
    (text: string, role: SpeechRole = 'default') => {
      if (!available || !text.trim()) return
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text.trim())
      utterance.lang = 'en-GB'
      const voice = pickVoice(role)
      if (voice) {
        utterance.voice = voice
        utterance.lang = voice.lang || 'en-GB'
      }
      if (role === 'caller') {
        // Slightly slower and lower to feel like a phone caller.
        utterance.rate = 0.92
        utterance.pitch = 0.75
      } else if (role === 'victim') {
        utterance.rate = 0.95
        utterance.pitch = 1.1
      } else {
        utterance.rate = 1
        utterance.pitch = 1
      }
      window.speechSynthesis.speak(utterance)
    },
    [available],
  )

  const stop = useCallback(() => {
    if (available) window.speechSynthesis.cancel()
  }, [available])

  // Speech is global to the browser: stop reading when the page that started it goes away.
  useEffect(
    () => () => {
      if (available) window.speechSynthesis.cancel()
    },
    [available],
  )

  return { available, voicesReady, speak, stop }
}
