import { describe, expect, it } from 'vitest'
import { buildSpans } from '../components/HighlightedText.tsx'

describe('buildSpans', () => {
  const text = 'Chase Fraud: reply YES or NO now'

  it('widens a partial quote to whole words', () => {
    const [s] = buildSpans(text, ['reply YE'])
    expect(text.slice(s.start, s.end)).toBe('reply YES')
  })

  it('keeps legend numbers when quotes overlap', () => {
    const spans = buildSpans(text, ['Chase Fraud: reply', 'Fraud', 'NO now'])
    expect(spans.map((s) => s.numbers)).toEqual([[1, 2], [3]])
  })

  it('matches case-insensitively and skips missing quotes', () => {
    const spans = buildSpans(text, ['missing', 'chase fraud'])
    expect(spans).toHaveLength(1)
    expect(spans[0].numbers).toEqual([2])
  })
})
