import { strings } from '../strings.ts'

export function PracticeBanner() {
  return (
    <div className="practice-banner" role="status">
      {strings.practiseBanner}
    </div>
  )
}