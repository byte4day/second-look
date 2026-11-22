import type { ReactNode } from 'react'

interface HighlightSpan {
  start: number
  end: number
  index: number
}

interface HighlightedTextProps {
  text: string
  quotes: string[]
}

function buildSpans(text: string, quotes: string[]): HighlightSpan[] {
  const spans: HighlightSpan[] = []
  let index = 1
  for (const quote of quotes) {
    if (!quote) continue
    const start = text.indexOf(quote)
    if (start === -1) continue
    // Skip overlapping
    if (spans.some((s) => start < s.end && start + quote.length > s.start)) continue
    spans.push({ start, end: start + quote.length, index: index++ })
  }
  spans.sort((a, b) => a.start - b.start)
  return spans
}

export function HighlightedText({ text, quotes }: HighlightedTextProps) {
  const spans = buildSpans(text, quotes)
  if (spans.length === 0) return <p>{text}</p>

  const parts: ReactNode[] = []
  let cursor = 0
  for (const span of spans) {
    if (span.start > cursor) {
      parts.push(text.slice(cursor, span.start))
    }
    parts.push(
      <mark key={span.index} className="highlight-mark">
        <span className="highlight-badge" aria-hidden="true">
          {span.index}
        </span>
        {text.slice(span.start, span.end)}
      </mark>,
    )
    cursor = span.end
  }
  if (cursor < text.length) parts.push(text.slice(cursor))

  return <p>{parts}</p>
}

export function ReasonLegend({
  reasons,
}: {
  reasons: { quote: string; why: string; flag: string }[]
}) {
  return (
    <ol className="red-flag-list">
      {reasons.map((reason, i) => (
        <li key={i}>
          <span className="highlight-badge" aria-hidden="true">
            {i + 1}
          </span>
          {reason.why}
        </li>
      ))}
    </ol>
  )
}
