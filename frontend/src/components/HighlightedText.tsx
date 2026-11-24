import type { ReactNode } from 'react'

interface HighlightSpan {
  start: number
  end: number
  /** Reason numbers (1-based) that point at this span, matching the legend. */
  numbers: number[]
}

interface HighlightedTextProps {
  text: string
  quotes: string[]
}

const isWordChar = (ch: string | undefined) => !!ch && /[\p{L}\p{N}'’]/u.test(ch)

/** Find a quote (case-insensitive) and widen it to whole words. */
function locate(text: string, quote: string): [number, number] | null {
  let start = text.indexOf(quote)
  if (start === -1) start = text.toLowerCase().indexOf(quote.toLowerCase())
  if (start === -1) return null
  let end = start + quote.length
  while (start > 0 && isWordChar(text[start - 1]) && isWordChar(text[start])) start--
  while (end < text.length && isWordChar(text[end]) && isWordChar(text[end - 1])) end++
  return [start, end]
}

export function buildSpans(text: string, quotes: string[]): HighlightSpan[] {
  let spans: HighlightSpan[] = []
  quotes.forEach((quote, i) => {
    const q = quote?.trim()
    if (!q) return
    const hit = locate(text, q)
    if (!hit) return
    let [start, end] = hit
    const numbers = [i + 1]
    // Merge with any span this one overlaps, keeping every reason number.
    const keep: HighlightSpan[] = []
    for (const s of spans) {
      if (start < s.end && end > s.start) {
        start = Math.min(start, s.start)
        end = Math.max(end, s.end)
        numbers.push(...s.numbers)
      } else {
        keep.push(s)
      }
    }
    spans = [...keep, { start, end, numbers: [...new Set(numbers)].sort((a, b) => a - b) }]
  })
  return spans.sort((a, b) => a.start - b.start)
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
      <mark key={span.start} className="highlight-mark">
        {span.numbers.map((n) => (
          <span key={n} className="highlight-badge" aria-hidden="true">
            {n}
          </span>
        ))}
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
