import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, TextArea, TextInput } from '../components/FormField.tsx'
import { useImageDownscale } from '../hooks/useImageDownscale.ts'
import { strings } from '../strings.ts'

const RESULT_KEY = 'scam_shield_last_result'
const SOURCE_KEY = 'scam_shield_last_source'

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
  const [photoBase64, setPhotoBase64] = useState<string | null>(null)
  const [mime, setMime] = useState('image/jpeg')
  const [fieldError, setFieldError] = useState<string | undefined>()

  const mutation = useMutation({
    mutationFn: async () => {
      if (!text.trim() && !photoBase64) {
        throw new Error('Add message text or a photo.')
      }
      if (photoBase64) {
        const result = await api.analyzeImage(photoBase64, mime)
        const source = text.trim() || '(Photo checked)'
        return { result, source }
      }
      const result = await api.analyzeText(text.trim())
      return { result, source: text.trim() }
    },
    onSuccess: ({ result, source }) => {
      saveCheckResult(result, source)
      navigate('/check/result')
    },
    onError: (err: Error) => {
      setFieldError(err.message.startsWith('Problem:') ? err.message : `Problem: ${err.message}`)
    },
  })

  const onPhoto = async (file: File | undefined) => {
    if (!file) {
      setPhotoName('')
      setPhotoBase64(null)
      return
    }
    setFieldError(undefined)
    try {
      const base64 = await downscaleToJpeg(file)
      setPhotoBase64(base64)
      setMime('image/jpeg')
      setPhotoName(file.name)
    } catch {
      setFieldError('Problem: Could not use that image.')
    }
  }

  return (
    <div className="page-column">
      <h1>{strings.checkTitle}</h1>
      <p>{strings.checkIntro}</p>
      <FormField id="message" label={strings.checkMessageLabel} error={fieldError}>
        <TextArea
          id="message"
          value={text}
          onChange={(e) => setText(e.target.value)}
          aria-invalid={fieldError ? true : undefined}
        />
      </FormField>
      <FormField id="photo" label={strings.checkPhotoLabel}>
        <TextInput
          id="photo"
          type="file"
          accept="image/*"
          capture="environment"
          onChange={(e) => void onPhoto(e.target.files?.[0])}
        />
        {photoName ? <p className="note">{photoName}</p> : null}
      </FormField>
      <Button
        variant="primary"
        block
        disabled={mutation.isPending}
        onClick={() => {
          setFieldError(undefined)
          mutation.mutate()
        }}
      >
        {strings.checkSubmit}
      </Button>
      {mutation.isPending ? <p role="status">{strings.checkWaiting}</p> : null}
    </div>
  )
}
