import { strings } from '../strings.ts'

export function PracticeBanner() {
  return (
    <div className="practice-banner" role="status">
      <div className="practice-banner__inner">{strings.practiseBanner}</div>
    </div>
  )
}
