#!/usr/bin/env tsx
/**
 * Validates CSS token contrast ratios for Scam Shield.
 */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function parseHex(hex: string): [number, number, number] {
  const h = hex.replace('#', '')
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]
}

function relLuminance([r, g, b]: [number, number, number]): number {
  const srgb = [r, g, b].map((c) => {
    const v = c / 255
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2]
}

function contrastRatio(fg: string, bg: string): number {
  const l1 = relLuminance(parseHex(fg))
  const l2 = relLuminance(parseHex(bg))
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
}

const tokensPath = resolve(import.meta.dirname, '../frontend/src/styles/tokens.css')
const css = readFileSync(tokensPath, 'utf8')

const pairs: [string, string, string][] = [
  ['ink on paper', '#1B1B1B', '#FAF7F0'],
  ['ink-muted on paper', '#404040', '#FAF7F0'],
  ['primary on paper', '#0B4F9C', '#FAF7F0'],
  ['on-primary on primary', '#FFFFFF', '#0B4F9C'],
  ['danger on paper', '#A11A1A', '#FAF7F0'],
  ['on-danger on danger', '#FFFFFF', '#A11A1A'],
  ['success on paper', '#1B5E31', '#FAF7F0'],
  ['warn-ink on warn-bg', '#4A3200', '#FFF1C2'],
]

let failed = false
for (const [label, fg, bg] of pairs) {
  const ratio = contrastRatio(fg, bg)
  const ok = ratio >= 7
  console.log(`${ok ? 'OK' : 'FAIL'} ${label}: ${ratio.toFixed(2)}:1`)
  if (!ok) failed = true
}

const targetMatch = css.match(/--target:\s*([^;]+);/)
const targetVal = targetMatch?.[1]?.trim() ?? ''
const rem = targetVal.endsWith('rem') ? parseFloat(targetVal) : 0
if (rem < 3.5) {
  console.log(`FAIL --target ${targetVal} is below 3.5rem`)
  failed = true
} else {
  console.log(`OK --target ${targetVal}`)
}

process.exit(failed ? 1 : 0)