import type { DrillSession } from '../api/types.ts'
import { useMutation } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, TextArea } from '../components/FormField.tsx'
import { strings } from '../strings.ts'

function loadSession(sessionId: string): DrillSession | null {
  const raw = sessionStorage.getItem(`drill_${sessionId}`)
  if (!raw) return null
  try {
    return JSON.parse(raw) as DrillSession
  } catch {
    return null
  }
}

function saveSession(session: DrillSession) {
  sessionStorage.setItem(`drill_${session.id}`, JSON.stringify(session))
}

export function PractiseChat() {
  const { sessionId = '' } = useParams()
  const navigate = useNavigate()
  const [message, setMessage] = useState('')
  const [recording, setRecording] = useState(false)
  const [turns, setTurns] = useState<{ role: string; content: string }[]>(() => {
    const session = loadSession(sessionId)
    if (session?.turns?.length) {
      return session.turns.map((t) => ({
        role: t.role === 'you' ? 'you' : t.role === 'victim' ? 'victim' : 'caller',
        content: t.content,
      }))
    }
    return []
  })
  const mediaRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const turnMutation = useMutation({
    mutationFn: () => api.drillTurn(sessionId, message.trim()),
    onSuccess: (data) => {
      setTurns((prev) => {
        const next = [...prev]
        next.push({ role: 'you', content: data.user_turn.content })
        if (data.caller_turn) {
          next.push({ role: 'caller', content: data.caller_turn.content })
        }
        saveSession({
          id: sessionId,
          scenario_id: '',
          difficulty: '',
          mode: '',
          status: data.finished ? 'finished' : 'active',
          turn_count: next.length,
          turns: [],
        })
        return next
      })
      setMessage('')
      if (data.finished) {
        sessionStorage.setItem(`debrief_pending_${sessionId}`, '1')
        navigate(`/practise/debrief/${sessionId}`)
      }
    },
  })

  const hangUp = useMutation({
    mutationFn: () => api.finishDrill(sessionId, true),
    onSuccess: (debrief) => {
      sessionStorage.setItem(`debrief_hungup_${sessionId}`, '1')
      sessionStorage.setItem(`debrief_${sessionId}`, JSON.stringify(debrief))
      navigate(`/practise/debrief/${sessionId}`)
    },
  })

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia) return
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const rec = new MediaRecorder(stream)
      chunksRef.current = []
      rec.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data)
      }
      rec.onstop = () => {
        void (async () => {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
          try {
            const { transcript } = await api.transcribeVoice(blob)
            setMessage((m) => (m ? `${m} ${transcript}` : transcript))
          } catch {
            window.dispatchEvent(
              new CustomEvent('scam-shield-banner', {
                detail: 'Voice could not be turned into text.',
              }),
            )
          }
          stream.getTracks().forEach((t) => t.stop())
        })()
      }
      mediaRef.current = rec
      setRecording(true)
      rec.start()
    } catch {
      window.dispatchEvent(
        new CustomEvent('scam-shield-banner', {
          detail: 'Microphone access is not available.',
        }),
      )
    }
  }

  const stopRecording = () => {
    mediaRef.current?.stop()
    setRecording(false)
  }

  const roleLabel = (role: string) =>
    role === 'caller' ? strings.practiseCaller : strings.practiseYou

  return (
    <div className="page-column">
      <h1>{strings.practiseTitle}</h1>
      <div className="chat-log" aria-live="polite">
        {turns.map((t, i) => (
          <p key={i}>
            <span className="chat-line__role">{roleLabel(t.role)}: </span>
            {t.content}
          </p>
        ))}
      </div>
      <FormField id="reply" label={strings.practiseMessageLabel}>
        <TextArea id="reply" value={message} onChange={(e) => setMessage(e.target.value)} />
      </FormField>
      <div className="stack">
        <Button
          variant="secondary"
          disabled={!message.trim() || turnMutation.isPending}
          onClick={() => turnMutation.mutate()}
        >
          {strings.practiseSend}
        </Button>
        <Button variant="secondary" onClick={recording ? stopRecording : () => void startRecording()}>
          {recording ? 'Stop recording' : strings.practiseRecordVoice}
        </Button>
        <p className="note">{strings.practiseRecordHint}</p>
        <Button variant="danger" block disabled={hangUp.isPending} onClick={() => hangUp.mutate()}>
          {strings.practiseHangUp}
        </Button>
      </div>
    </div>
  )
}