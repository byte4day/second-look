function parseHex(hex: string): [number, number, number] {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return [r, g, b]
}

function relLuminance([r, g, b]: [number, number, number]): number {
  const srgb = [r, g, b].map((c) => {
    const v = c / 255
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2]
}

export function contrastRatio(foreground: string, background: string): number {
  const l1 = relLuminance(parseHex(foreground))
  const l2 = relLuminance(parseHex(background))
  const lighter = Math.max(l1, l2)
  const darker = Math.min(l1, l2)
  return (lighter + 0.05) / (darker + 0.05)
}

export const tokenPairs: [string, string, string][] = [
  ['ink on paper', '#1B1B1B', '#FAF7F0'],
  ['ink-muted on paper', '#404040', '#FAF7F0'],
  ['primary on paper', '#0B4F9C', '#FAF7F0'],
  ['on-primary on primary', '#FFFFFF', '#0B4F9C'],
  ['danger on paper', '#A11A1A', '#FAF7F0'],
  ['on-danger on danger', '#FFFFFF', '#A11A1A'],
  ['success on paper', '#1B5E31', '#FAF7F0'],
  ['warn-ink on warn-bg', '#4A3200', '#FFF1C2'],
]

export const TARGET_MIN_REM = 3.5