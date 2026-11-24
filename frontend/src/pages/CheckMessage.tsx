import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, TextArea, TextInput } from '../components/FormField.tsx'
import { useImageDownscale } from '../hooks/useImageDownscale.ts'
import { BitSays } from '../components/Bit.tsx'
import { strings } from '../strings.ts'

const RESULT_KEY = 'scam_shield_last_result'
const SOURCE_KEY = 'scam_shield_last_source'

const DEMO_SCAM =
  'Chase Fraud: Did you write a check for $5,000.00? Please reply YES or NO. Msg & data rates may apply.'
const MAX_MESSAGE_CHARS = 8000

const DEMO_OK = 'Hi mum, I will call you later about Sunday lunch. Love you.'

export function saveCheckResult(result: unknown, sourceText: string) {
  sessionStorage.setItem(RESULT_KEY, JSON.stringify(result))
  sessionStorage.setItem(SOURCE_KEY, sourceText)
}

export function loadCheckResult(): { result: import('../api/types.ts').AnalyzeResult; source: string } | null {
  const raw = sessionStorage.getItem(RESULT_KEY)
  const source = sessionStorage.getItem(SOURCE_KEY)
  if (!raw || !source) return null
  try {
    return { result: JSON.parse(raw) as import('../api/types.ts').AnalyzeResult, source }
  } catch {
    return null
  }
}

export function CheckMessage() {
  const navigate = useNavigate()
  const { downscaleToJpeg } = useImageDownscale()
  const [text, setText] = useState('')
  const [photoName, setPhotoName] = useState('')
  const [photoNote, setPhotoNote] = useState<string | undefined>()
  const [readingPhoto, setReadingPhoto] = useState(false)
  const [fieldError, setFieldError] = useState<string | undefined>()

  const mutation = useMutation({
    mutationFn: async () => {
      if (!text.trim()) {
        throw new Error('Add message text or a photo.')
      }
      const result = await api.analyzeText(text.trim())
      return { result, source: text.trim() }
    },
    onSuccess: ({ result, source }) => {
      saveCheckResult(result, source)
      navigate('/check/result')
    },
    onError: (err: Error) => {
      setFieldError(err.message.replace(/^Problem:\s*/, ''))
    },
  })

  const onPhoto = async (file: File | undefined) => {
    if (!file) {
      setPhotoName('')
      setPhotoNote(undefined)
      return
    }
    setFieldError(undefined)
    setPhotoNote(undefined)
    setReadingPhoto(true)
    try {
      const base64 = await downscaleToJpeg(file)
      setPhotoName(file.name)
      const ocr = await api.extractTextFromImage(base64, 'image/jpeg')
      if (ocr.found && ocr.text.trim()) {
        setText(ocr.text.trim().slice(0, MAX_MESSAGE_CHARS))
        setPhotoNote(strings.checkPhotoFilled)
      } else {
        setPhotoNote(strings.checkPhotoEmpty)
      }
    } catch {
      setFieldError('We could not use that image. Try another photo, or type the message.')
      setPhotoNote(undefined)
    } finally {
      setReadingPhoto(false)
    }
  }

  const busy = mutation.isPending || readingPhoto

  return (
    <div className="page-column">
      <h1>{strings.checkTitle}</h1>
      <p className="page-lead">{strings.checkIntro}</p>
      <div className="demo-chips" role="group" aria-label={strings.checkTrySamples}>
        <p className="note">{strings.checkTrySamples}</p>
        <Button
          variant="secondary"
          compact
          disabled={busy}
          onClick={() => {
            setText(DEMO_SCAM)
            setFieldError(undefined)
          }}
        >
          {strings.checkSampleScam}
        </Button>
        <Button
          variant="secondary"
          compact
          disabled={busy}
          onClick={() => {
            setText(DEMO_OK)
            setFieldError(undefined)
          }}
        >
          {strings.checkSampleOk}
        </Button>
      </div>
      <h2 className="step-heading">
        <span className="num-tag" aria-hidden="true">1</span>
        <span>Add the message</span>
      </h2>
      <div className="panel">
        <FormField id="photo" label={strings.checkPhotoLabel}>
          <TextInput
            id="photo"
            type="file"
            accept="image/*"
            capture="environment"
            disabled={busy}
            onChange={(e) => void onPhoto(e.target.files?.[0])}
          />
          {photoName ? <p className="note">{photoName}</p> : null}
          {readingPhoto ? (
            <p className="note" role="status">
              {strings.checkPhotoReading}
            </p>
          ) : null}
          {photoNote && !readingPhoto ? (
            <p className="note" role="status">
              {photoNote}
            </p>
          ) : null}
        </FormField>
        <FormField id="message" label={strings.checkMessageLabel} error={fieldError}>
          <TextArea
            id="message"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={MAX_MESSAGE_CHARS}
            aria-describedby={fieldError ? 'message-error' : undefined}
            aria-invalid={fieldError ? true : undefined}
            disabled={readingPhoto}
          />
        </FormField>
      </div>
      <BitSays mood="thinking" size={64}>
        <p>{strings.bitCheckTip}</p>
      </BitSays>
      <h2 className="step-heading">
        <span className="num-tag" aria-hidden="true">2</span>
        <span>Check it</span>
      </h2>
      <Button
        variant="primary"
        block
        disabled={busy}
        onClick={() => {
          setFieldError(undefined)
          mutation.mutate()
        }}
      >
        {strings.checkSubmit}
      </Button>
      {mutation.isPending ? (
        <p className="panel" role="status">
          {strings.checkWaiting}
        </p>
      ) : null}
    </div>
  )
}
