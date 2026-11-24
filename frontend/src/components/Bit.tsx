import type { ReactNode } from 'react'

/**
 * Bit — Scam Shield's pixel-art mascot: a small shield with a face.
 * Drawn on a 16×18 grid so it stays crisp at any size. Purely decorative:
 * whatever Bit "says" is real text next to it, so screen readers get the words.
 */
export type BitMood = 'happy' | 'worried' | 'thinking' | 'calm'

const FILL: Record<string, string> = {
  K: 'var(--bit-outline)',
  G: 'var(--bit-rim)',
  B: 'var(--bit-body)',
  L: 'var(--bit-shine)',
  W: 'var(--bit-face)',
  E: 'var(--bit-outline)',
  P: 'var(--bit-cheek)',
  S: 'var(--bit-sweat)',
}

// Rows 0–4 and 10–17 never change; rows 5–9 are the face and carry the mood.
const TOP = [
  '....KKKKKKKK....',
  '..KKGGGGGGGGKK..',
  '.KGBBBBBBBBBBGK.',
  'KGBLLBBBBBBBBBGK',
  'KGBLBBBBBBBBBBGK',
]
const BOTTOM = [
  '.KGBBWWWWWWBBGK.',
  '.KGBBBWWWWBBBGK.',
  '..KGBBBBBBBBGK..',
  '...KGBBBBBBGK...',
  '....KGBBBBGK....',
  '.....KGBBGK.....',
  '......KGGK......',
  '.......KK.......',
]
const FACES: Record<BitMood, string[]> = {
  happy: [
    'KGBBWWWWWWWWBBGK',
    'KGBBWEWWWWEWBBGK',
    'KGBBWEWWWWEWBBGK',
    'KGBBWWWWWWWWBBGK',
    'KGBBWPKWWKPWBBGK',
  ],
  calm: [
    'KGBBWWWWWWWWBBGK',
    'KGBBWEWWWWEWBBGK',
    'KGBBWEWWWWEWBBGK',
    'KGBBWWWWWWWWBBGK',
    'KGBBWPWKKWPWBBGK',
  ],
  worried: [
    'KGBBWKWWWWKWBBGK',
    'KGBBWEWWWWEWBBGK',
    'KGBBWEWWWWEWSBGK',
    'KGBBWWWWWWWWSBGK',
    'KGBBWWKKKKWWBBGK',
  ],
  thinking: [
    'KGBBWWWWWKKWBBGK',
    'KGBBWWEWWWEWBBGK',
    'KGBBWWEWWWEWBBGK',
    'KGBBWWWWWWWWBBGK',
    'KGBBWWWWKKKWBBGK',
  ],
}

function rects(mood: BitMood) {
  const rows = [...TOP, ...FACES[mood], ...BOTTOM]
  const out: { x: number; y: number; c: string; eye: boolean }[] = []
  rows.forEach((row, y) =>
    [...row].forEach((ch, x) => {
      if (ch !== '.') out.push({ x, y, c: FILL[ch], eye: ch === 'E' })
    }),
  )
  return out
}

export function Bit({
  mood = 'happy',
  size = 96,
  className = '',
}: {
  mood?: BitMood
  size?: number
  className?: string
}) {
  return (
    <svg
      className={`bit bit--${mood} ${className}`.trim()}
      width={size}
      height={(size * 18) / 16}
      viewBox="0 0 16 18"
      shapeRendering="crispEdges"
      aria-hidden="true"
      focusable="false"
    >
      {rects(mood).map(({ x, y, c, eye }) => (
        <rect
          key={`${x}-${y}`}
          x={x}
          y={y}
          width={1}
          height={1}
          fill={c}
          className={eye ? 'bit__eye' : undefined}
        />
      ))}
    </svg>
  )
}

/** Bit with a speech bubble. The bubble holds real text for everyone. */
export function BitSays({
  mood = 'happy',
  children,
  size = 88,
}: {
  mood?: BitMood
  children: ReactNode
  size?: number
}) {
  return (
    <div className={`bit-says bit-says--${mood}`}>
      <Bit mood={mood} size={size} />
      <div className="bit-says__bubble">
        <p className="bit-says__name">Bit says</p>
        <div className="bit-says__text">{children}</div>
      </div>
    </div>
  )
}
