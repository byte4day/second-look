import { useQuery, useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, SelectInput } from '../components/FormField.tsx'
import { strings } from '../strings.ts'

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
    mutationFn: () => {
      const id = scenarioId || scenarios[0]?.id
      if (!id) throw new Error('No scenarios available.')
      return api.createDrill(id, difficulty, mode)
    },
    onSuccess: (session) => {
      sessionStorage.setItem(`drill_${session.id}`, JSON.stringify(session))
      navigate(`/practise/chat/${session.id}`)
    },
  })

  return (
    <div className="page-column">
      <h1>{strings.practiseTitle}</h1>
      <p>{strings.practiseIntro}</p>
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
        variant="primary"
        block
        disabled={!scenarios.length || start.isPending}
        onClick={() => start.mutate()}
      >
        {strings.practiseStart}
      </Button>
    </div>
  )
}