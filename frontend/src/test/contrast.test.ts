import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
import { describe, expect, it } from 'vitest'
import { TARGET_MIN_REM, contrastRatio, tokenPairs } from './contrast.ts'

describe('design token contrast', () => {
  it('meets 7:1 for text pairs', () => {
    for (const [label, fg, bg] of tokenPairs) {
      const ratio = contrastRatio(fg, bg)
      expect(ratio, `${label} contrast ${ratio.toFixed(2)}`).toBeGreaterThanOrEqual(7)
    }
  })

  it('keeps touch target at least 3.5rem', () => {
    const css = readFileSync(resolve(__dirname, '../styles/tokens.css'), 'utf8')
    const match = css.match(/--target:\s*([^;]+);/)
    expect(match).toBeTruthy()
    const value = match![1].trim()
    const rem = value.endsWith('rem') ? parseFloat(value) : 0
    expect(rem).toBeGreaterThanOrEqual(TARGET_MIN_REM)
  })
})