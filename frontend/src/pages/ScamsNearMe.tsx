import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { lazy, Suspense, useState } from 'react'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { FormField, SelectInput, TextArea } from '../components/FormField.tsx'
import { strings } from '../strings.ts'

const MapView = lazy(() =>
  import('../components/ScamsMap.tsx').then((m) => ({ default: m.ScamsMap })),
)

function typeLabel(value: string): string {
  return strings.scamTypes.find((t) => t.value === value)?.label ?? value
}

const REPORT_AREAS = strings.areas.filter((a) => a.value !== 'generic')
const MAX_DETAILS = 200

export function ScamsNearMe() {
  const [area, setArea] = useState('generic')
  const [reportArea, setReportArea] = useState<string>(REPORT_AREAS[0]?.value ?? 'england')
  const [showMap, setShowMap] = useState(false)
  const [scamType, setScamType] = useState('phone')
  const [details, setDetails] = useState('')
  const [fieldError, setFieldError] = useState<string | undefined>()
  const [sent, setSent] = useState(false)
  const queryClient = useQueryClient()

  const summary = useQuery({
    queryKey: ['report-summary', area],
    queryFn: () => api.reportSummary(area),
  })

  const report = useMutation({
    mutationFn: () => api.createReport(scamType, reportArea, details.trim() || undefined),
    onSuccess: () => {
      setDetails('')
      setFieldError(undefined)
      setSent(true)
      void queryClient.invalidateQueries({ queryKey: ['report-summary'] })
    },
    onError: (err: Error) => setFieldError(err.message),
  })

  const maxCount = Math.max(1, ...(summary.data?.items.map((i) => i.count) ?? [1]))

  return (
    <div className="page-column">
      <h1>{strings.scamsTitle}</h1>
      <p className="page-lead">{strings.scamsUnverified}</p>
      <FormField id="area" label={strings.scamsArea}>
        <SelectInput
          id="area"
          value={area}
          onChange={(e) => {
            setArea(e.target.value)
            if (e.target.value !== 'generic') setReportArea(e.target.value)
          }}
        >
          {strings.areas.map((a) => (
            <option key={a.value} value={a.value}>
              {a.label}
            </option>
          ))}
        </SelectInput>
      </FormField>
      <section className="panel">
        <h2>{strings.scamsSummary}</h2>
        {summary.isLoading ? <p>{strings.loading}</p> : null}
        {summary.isError ? <p role="alert">{summary.error.message}</p> : null}
        {summary.data ? (
          <>
            <p>
              <strong>
                {strings.scamsTotal}: {summary.data.total}
              </strong>
            </p>
            <p className="note">{summary.data.label}</p>
            {!summary.data.enough || summary.data.items.length === 0 ? (
              <p>{summary.data.message_plain || strings.scamsNoReports}</p>
            ) : (
              <ul className="stat-bars">
                {summary.data.items.map((item) => (
                  <li key={item.scam_type}>
                    <div className="stat-bars__label">
                      <span>{typeLabel(item.scam_type)}</span>
                      <span>{item.count}</span>
                    </div>
                    <div className="stat-bars__track" aria-hidden="true">
                      <div
                        className="stat-bars__fill"
                        style={{ width: `${Math.round((item.count / maxCount) * 100)}%` }}
                      />
                    </div>
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
      <section className="panel">
        <h2>{strings.scamsReportDetails}</h2>
        <p className="note">{strings.scamsEmptyHint}</p>
        {sent ? <p role="status">{strings.scamsReportThanks}</p> : null}
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
          <SelectInput
            id="report-area"
            value={reportArea}
            onChange={(e) => setReportArea(e.target.value)}
          >
            {REPORT_AREAS.map((a) => (
              <option key={a.value} value={a.value}>
                {a.label}
              </option>
            ))}
          </SelectInput>
        </FormField>
        <FormField id="details" label={strings.scamsReportDetails}>
          <TextArea
            id="details"
            value={details}
            maxLength={MAX_DETAILS}
            aria-describedby="details-count"
            onChange={(e) => {
              setDetails(e.target.value)
              setSent(false)
            }}
          />
          <p className="note" id="details-count">
            {details.length} of {MAX_DETAILS} letters used
          </p>
        </FormField>
        <Button variant="primary" block disabled={report.isPending} onClick={() => report.mutate()}>
          {strings.scamsReportSubmit}
        </Button>
      </section>
    </div>
  )
}
