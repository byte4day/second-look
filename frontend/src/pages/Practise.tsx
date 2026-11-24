import { useQuery, useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, SelectInput } from '../components/FormField.tsx'
import { strings } from '../strings.ts'

const START_FAILED = 'The practice could not start.'

export function Practise() {
  const navigate = useNavigate()
  const { data: scenarios = [], isLoading } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.listScenarios(),
  })
  const [scenarioId, setScenarioId] = useState('')
  const [difficulty, setDifficulty] = useState<'easy' | 'hard'>('easy')
  const [mode, setMode] = useState<'experience' | 'helper'>('experience')

  const start = useMutation({
    mutationFn: (opts?: { scenario?: string; difficulty?: string; mode?: string }) => {
      const id = opts?.scenario || scenarioId || scenarios[0]?.id
      if (!id) throw new Error('No scenarios available.')
      return api.createDrill(
        id,
        opts?.difficulty || difficulty,
        opts?.mode || mode,
      )
    },
    onSuccess: (session) => {
      sessionStorage.setItem(`drill_${session.id}`, JSON.stringify(session))
      navigate(`/practise/chat/${session.id}`)
    },
  })
  const startError = start.isError ? start.error.message : null

  const bankId =
    scenarios.find((s) => s.id === 'bank_otp')?.id ||
    scenarios.find((s) => /bank/i.test(s.title))?.id

  return (
    <div className="page-column">
      <h1>{strings.practiseTitle}</h1>
      <p className="page-lead">{strings.practiseIntro}</p>
      {bankId ? (
        <div className="panel">
          <p className="note">{strings.practiseQuickHint}</p>
          <Button
            variant="primary"
            block
            disabled={start.isPending}
            onClick={() =>
              start.mutate({ scenario: bankId, difficulty: 'easy', mode: 'experience' })
            }
          >
            {strings.practiseQuickStart}
          </Button>
        </div>
      ) : null}
      {isLoading ? <p>{strings.loading}</p> : null}
      <FormField id="scenario" label={strings.practiseScenario}>
        <SelectInput
          id="scenario"
          value={scenarioId || scenarios[0]?.id || ''}
          onChange={(e) => setScenarioId(e.target.value)}
        >
          {scenarios.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title}
            </option>
          ))}
        </SelectInput>
      </FormField>
      <FormField id="difficulty" label={strings.practiseDifficulty}>
        <SelectInput
          id="difficulty"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value as 'easy' | 'hard')}
        >
          <option value="easy">{strings.practiseDifficultyEasy}</option>
          <option value="hard">{strings.practiseDifficultyHard}</option>
        </SelectInput>
      </FormField>
      <FormField id="mode" label={strings.practiseMode}>
        <SelectInput
          id="mode"
          value={mode}
          onChange={(e) => setMode(e.target.value as 'experience' | 'helper')}
        >
          <option value="experience">{strings.practiseModeExperience}</option>
          <option value="helper">{strings.practiseModeHelper}</option>
        </SelectInput>
      </FormField>
      <Button
        variant="secondary"
        block
        disabled={!scenarios.length || start.isPending}
        onClick={() => start.mutate({})}
      >
        {strings.practiseStart}
      </Button>
      {start.isPending ? (
        <p className="note" role="status">
          {strings.loading}
        </p>
      ) : null}
      {startError ? (
        <p className="note" role="alert">
          {START_FAILED} {startError}
        </p>
      ) : null}
    </div>
  )
}
