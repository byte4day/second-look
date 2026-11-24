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
  ['ink on paper', '#14201A', '#F3F5F2'],
  ['ink-muted on paper', '#2A3A32', '#F3F5F2'],
  ['primary on paper', '#0A4D8C', '#F3F5F2'],
  ['on-primary on primary', '#FFFFFF', '#0A4D8C'],
  ['danger on paper', '#9B1C1C', '#F3F5F2'],
  ['on-danger on danger', '#FFFFFF', '#9B1C1C'],
  ['success on paper', '#145A32', '#F3F5F2'],
  ['warn-ink on warn-bg', '#3D2E00', '#FFF4CC'],
]

export const TARGET_MIN_REM = 3.5
