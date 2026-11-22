import { useCallback } from 'react'

export function useSpeech() {
  const available = typeof window !== 'undefined' && 'speechSynthesis' in window

  const speak = useCallback((text: string) => {
    if (!available) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'en-GB'
    window.speechSynthesis.speak(utterance)
  }, [available])

  const stop = useCallback(() => {
    if (available) window.speechSynthesis.cancel()
  }, [available])

  return { available, speak, stop }
}