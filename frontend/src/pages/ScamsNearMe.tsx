import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { lazy, Suspense, useState } from 'react'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, SelectInput, TextArea, TextInput } from '../components/FormField.tsx'
import { strings } from '../strings.ts'

const MapView = lazy(() =>
  import('../components/ScamsMap.tsx').then((m) => ({ default: m.ScamsMap })),
)

export function ScamsNearMe() {
  const [area, setArea] = useState('generic')
  const [showMap, setShowMap] = useState(false)
  const [scamType, setScamType] = useState('phone')
  const [details, setDetails] = useState('')
  const [fieldError, setFieldError] = useState<string | undefined>()
  const queryClient = useQueryClient()

  const summary = useQuery({
    queryKey: ['report-summary', area],
    queryFn: () => api.reportSummary(area),
  })

  const report = useMutation({
    mutationFn: () => api.createReport(scamType, area, details || undefined),
    onSuccess: () => {
      setDetails('')
      setFieldError(undefined)
      void queryClient.invalidateQueries({ queryKey: ['report-summary'] })
    },
    onError: (err: Error) => setFieldError(err.message),
  })

  return (
    <div className="page-column">
      <h1>{strings.scamsTitle}</h1>
      <FormField id="area" label={strings.scamsArea}>
        <SelectInput id="area" value={area} onChange={(e) => setArea(e.target.value)}>
          {strings.areas.map((a) => (
            <option key={a.value} value={a.value}>
              {a.label}
            </option>
          ))}
        </SelectInput>
      </FormField>
      <section>
        <h2>{strings.scamsSummary}</h2>
        {summary.isLoading ? <p>{strings.loading}</p> : null}
        {summary.data ? (
          <>
            <p>
              {strings.scamsTotal}: {summary.data.total}
            </p>
            <p className="note">{summary.data.label}</p>
            {!summary.data.enough || summary.data.items.length === 0 ? (
              <p>{summary.data.message_plain || strings.scamsNoReports}</p>
            ) : (
              <ul>
                {summary.data.items.map((item) => (
                  <li key={item.scam_type}>
                    {item.scam_type}: {item.count}
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : null}
      </section>
      <Button variant="secondary" onClick={() => setShowMap((v) => !v)}>
        {showMap ? strings.scamsHideMap : strings.scamsShowMap}
      </Button>
      {showMap ? (
        <Suspense fallback={<div className="map-placeholder">{strings.loading}</div>}>
          <MapView area={area} />
        </Suspense>
      ) : null}
      <section>
        <h2>{strings.scamsReportDetails}</h2>
        <FormField id="stype" label={strings.scamsReportType} error={fieldError}>
          <SelectInput
            id="stype"
            value={scamType}
            onChange={(e) => setScamType(e.target.value)}
          >
            {strings.scamTypes.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </SelectInput>
        </FormField>
        <FormField id="report-area" label={strings.scamsReportArea}>
          <TextInput id="report-area" value={area} readOnly />
        </FormField>
        <FormField id="details" label={strings.scamsReportDetails}>
          <TextArea id="details" value={details} onChange={(e) => setDetails(e.target.value)} />
        </FormField>
        <Button variant="primary" block disabled={report.isPending} onClick={() => report.mutate()}>
          {strings.scamsReportSubmit}
        </Button>
      </section>
    </div>
  )
}