import { strings } from '../strings.ts'

export function SkipLink() {
  return (
    <a href="#main-content" className="skip-link">
      {strings.skipToContent}
    </a>
  )
}