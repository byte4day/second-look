import type { DrillSession } from '../api/types.ts'
import { useMutation } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, TextArea } from '../components/FormField.tsx'
import { useCallerVoice, type CallerPersona } from '../hooks/useCallerVoice.ts'
import { strings } from '../strings.ts'

const VOICE_PREF_KEY = 'scam_shield_caller_voice'

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
  try {
    sessionStorage.setItem(`drill_${session.id}`, JSON.stringify(session))
  } catch {
    // Storage full or blocked: the chat still works, it just will not survive a refresh.
  }
}

type ChatTurn = { role: string; content: string }

function recorderFile(mimeType: string): { type: string; name: string } {
  const type = mimeType || 'audio/webm'
  if (type.includes('mp4')) return { type, name: 'voice.mp4' }
  if (type.includes('ogg')) return { type, name: 'voice.ogg' }
  if (type.includes('wav')) return { type, name: 'voice.wav' }
  return { type, name: 'voice.webm' }
}

const SAFETY_TITLE = 'Please use pretend details only.'

function loadVoiceOn(): boolean {
  try {
    const raw = localStorage.getItem(VOICE_PREF_KEY)
    if (raw === null) return true
    return raw === '1'
  } catch {
    return true
  }
}

function personaFor(role: string): CallerPersona {
  return role === 'victim' ? 'victim' : 'caller'
}

export function PractiseChat() {
  const { sessionId = '' } = useParams()
  const navigate = useNavigate()
  const { play, stop, busy, lastEngine, error: voiceError } = useCallerVoice()
  const [message, setMessage] = useState('')
  const [recording, setRecording] = useState(false)
  const [callerVoiceOn, setCallerVoiceOn] = useState(loadVoiceOn)
  const [status, setStatus] = useState<string | null>(null)
  const [warning, setWarning] = useState<string | null>(null)
  const [turns, setTurns] = useState<ChatTurn[]>(() => {
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
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const logRef = useRef<HTMLDivElement | null>(null)
  const discardRecordingRef = useRef(false)

  // Keep the whole conversation in sessionStorage so a refresh does not wipe it.
  useEffect(() => {
    if (!sessionId) return
    const saved = loadSession(sessionId)
    saveSession({
      id: sessionId,
      scenario_id: saved?.scenario_id ?? '',
      difficulty: saved?.difficulty ?? '',
      mode: saved?.mode ?? '',
      status: saved?.status ?? 'active',
      turn_count: turns.length,
      turns: turns.map((t, i) => ({ id: i, role: t.role, content: t.content })),
    })
  }, [sessionId, turns])

  // Show the newest line without the user having to scroll the chat box.
  useEffect(() => {
    const el = logRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [turns])

  // Release the microphone if the user leaves while recording.
  useEffect(
    () => () => {
      discardRecordingRef.current = true
      const rec = mediaRef.current
      if (rec && rec.state !== 'inactive') {
        try {
          rec.stop()
        } catch {
          // already stopped
        }
      }
      streamRef.current?.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    },
    [],
  )

  const speakLine = (role: string, content: string) => {
    if (!callerVoiceOn) return
    setStatus(strings.practiseVoicePlaying)
    void play(content, personaFor(role)).then(() => setStatus(null))
  }

  // Status is reset by the toggle button itself; this only persists and silences.
  useEffect(() => {
    try {
      localStorage.setItem(VOICE_PREF_KEY, callerVoiceOn ? '1' : '0')
    } catch {
      // Storage blocked: the choice lasts for this visit only.
    }
    if (!callerVoiceOn) stop()
  }, [callerVoiceOn, stop])

  useEffect(() => () => stop(), [stop])

  const turnMutation = useMutation({
    mutationFn: () => api.drillTurn(sessionId, message.trim()),
    onSuccess: (data) => {
      const added: ChatTurn[] = [{ role: 'you', content: data.user_turn.content }]
      let reply: ChatTurn | null = null
      if (data.caller_turn) {
        reply = {
          role: data.caller_turn.role === 'victim' ? 'victim' : 'caller',
          content: data.caller_turn.content,
        }
        added.push(reply)
      }
      setTurns((prev) => [...prev, ...added])
      setWarning(data.warning || null)
      setMessage('')
      if (reply && !data.finished) speakLine(reply.role, reply.content)
      if (data.finished) {
        stop()
        sessionStorage.setItem(`debrief_pending_${sessionId}`, '1')
        navigate(`/practise/debrief/${sessionId}`)
      }
    },
  })

  const hangUp = useMutation({
    mutationFn: () => {
      stop()
      discardRecordingRef.current = true
      if (mediaRef.current && mediaRef.current.state !== 'inactive') mediaRef.current.stop()
      setRecording(false)
      return api.finishDrill(sessionId, true)
    },
    onSuccess: (debrief) => {
      sessionStorage.setItem(`debrief_hungup_${sessionId}`, '1')
      sessionStorage.setItem(`debrief_${sessionId}`, JSON.stringify(debrief))
      navigate(`/practise/debrief/${sessionId}`)
    },
  })

  const releaseStream = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
  }

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      window.dispatchEvent(
        new CustomEvent('scam-shield-banner', {
          detail: 'Voice recording is not available on this device. You can type instead.',
        }),
      )
      return
    }
    try {
      stop()
      discardRecordingRef.current = false
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const rec = new MediaRecorder(stream)
      chunksRef.current = []
      rec.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data)
      }
      rec.onstop = () => {
        releaseStream()
        if (discardRecordingRef.current) return
        void (async () => {
          const file = recorderFile(rec.mimeType)
          const blob = new Blob(chunksRef.current, { type: file.type })
          if (!blob.size) return
          try {
            const { transcript } = await api.transcribeVoice(blob, file.name)
            setMessage((m) => (m ? `${m} ${transcript}` : transcript))
          } catch {
            window.dispatchEvent(
              new CustomEvent('scam-shield-banner', {
                detail: 'Voice could not be turned into text. You can type instead.',
              }),
            )
          }
        })()
      }
      mediaRef.current = rec
      setRecording(true)
      rec.start()
    } catch {
      releaseStream()
      setRecording(false)
      window.dispatchEvent(
        new CustomEvent('scam-shield-banner', {
          detail: 'Microphone access is not available.',
        }),
      )
    }
  }

  const stopRecording = () => {
    if (mediaRef.current && mediaRef.current.state !== 'inactive') mediaRef.current.stop()
    setRecording(false)
  }

  const roleLabel = (role: string) => {
    if (role === 'caller') return strings.practiseCaller
    if (role === 'victim') return strings.practiseVictim
    return strings.practiseYou
  }

  const engineNote =
    lastEngine === 'orpheus'
      ? strings.practiseVoiceEngineOrpheus
      : lastEngine === 'neural'
        ? strings.practiseVoiceEngineNeural
        : lastEngine === 'phone_fallback'
          ? strings.practiseVoiceEnginePhone
          : lastEngine === 'browser'
            ? strings.practiseVoiceEngineBrowser
            : null

  return (
    <div className="page-column">
      <h1>{strings.practiseTitle}</h1>
      <div className="stack">
        <Button
          variant="secondary"
          block
          onClick={() => {
            const next = !callerVoiceOn
            setCallerVoiceOn(next)
            if (next) {
              const first = turns.find((t) => t.role === 'caller' || t.role === 'victim')
              if (first) {
                setStatus(strings.practiseVoicePlaying)
                void play(first.content, personaFor(first.role)).then(() => setStatus(null))
              }
            } else {
              stop()
              setStatus(null)
            }
          }}
        >
          {callerVoiceOn ? strings.practiseVoiceOn : strings.practiseVoiceOff}
        </Button>
        <p className="note">{strings.practiseVoiceHint}</p>
        {status || busy ? (
          <p className="note" role="status">
            {status || strings.practiseVoicePlaying}
          </p>
        ) : null}
        {engineNote ? <p className="note">{engineNote}</p> : null}
        {voiceError ? (
          <p className="note" role="alert">
            {voiceError}
          </p>
        ) : null}
      </div>
      <div
        className="chat-log"
        role="log"
        aria-live="polite"
        aria-label="Practice conversation"
        tabIndex={0}
        ref={logRef}
      >
        {turns.map((t, i) => (
          <div
            key={i}
            className={
              t.role === 'you'
                ? 'chat-line chat-line--you'
                : t.role === 'victim'
                  ? 'chat-line chat-line--victim'
                  : 'chat-line chat-line--caller'
            }
          >
            <p>
              <span className="chat-line__role">{roleLabel(t.role)}</span>
              {t.content}
            </p>
            {t.role === 'caller' || t.role === 'victim' ? (
              <div className="chat-actions">
                <Button
                  variant="secondary"
                  compact
                  disabled={busy}
                  onClick={() => {
                    setStatus(strings.practiseVoicePlaying)
                    void play(t.content, personaFor(t.role)).then(() => setStatus(null))
                  }}
                >
                  {strings.practiseListen}
                </Button>
              </div>
            ) : null}
          </div>
        ))}
      </div>
      {warning ? (
        <div className="panel" role="alert">
          <p>
            <strong>{SAFETY_TITLE}</strong> {warning}
          </p>
        </div>
      ) : null}
      <FormField id="reply" label={strings.practiseMessageLabel}>
        <TextArea
          id="reply"
          value={message}
          maxLength={2000}
          onChange={(e) => setMessage(e.target.value)}
        />
      </FormField>
      <div className="sticky-actions">
        <Button
          variant="primary"
          block
          disabled={!message.trim() || turnMutation.isPending}
          onClick={() => turnMutation.mutate()}
        >
          {strings.practiseSend}
        </Button>
        <Button
          variant="secondary"
          block
          onClick={recording ? stopRecording : () => void startRecording()}
        >
          {recording ? strings.practiseStopRecording : strings.practiseRecordVoice}
        </Button>
        {recording ? (
          <p className="note" role="status">
            {strings.practiseRecording}
          </p>
        ) : null}
        <p className="note">{strings.practiseRecordHint}</p>
        <Button variant="danger" block disabled={hangUp.isPending} onClick={() => hangUp.mutate()}>
          {strings.practiseHangUp}
        </Button>
      </div>
    </div>
  )
}
