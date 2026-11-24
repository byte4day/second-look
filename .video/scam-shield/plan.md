# Scam Shield — film plan

## Logline

Imposter scams hit older adults through the phone first — then Scam Shield shows a calm path: check a message, practise hanging up, get help now, and prove it with green tests for the judges.

## Format

| | |
| --- | --- |
| Format | `explainer` (app-demo spine) |
| Engine | Remotion |
| Aspect | 16:9 |
| Duration | 55s @ 30 fps |
| Audience | Hackathon judges |
| Caption lang | en |

## Tone

Civic-trust leaflet: paper quiet, shield blue, ink-dark type. Never shame older adults. Scammers are professionals; stopping is always a good move. Large readable UI holds; no neon/AI-gradient sizzle.

## Message arc

1. **Problem (0–13s)** — Older adults + phone imposter threat; one FTC 2024 sourced line; dignity close.
2. **Solution (13–50s)** — Live UI: Home → Check (sample → Likely a scam) → Practise bank fraud → Help now (Action Fraud) → brief green tests.
3. **CTA (50–55s)** — Calm guide for judges; `DEMO_MODE` clone-and-run.

## Energy curve

| Beat | Energy | Feel |
| --- | --- | --- |
| Hook / problem | Low–medium | Still paper, serious type, slow push |
| Tone bridge | Soft resolve | Dignity line before product |
| App proof | Steady medium | Cursor clarity, readable holds |
| Tests flash | Brief lift | Terminal green = credibility |
| CTA | Calm close | Brand + DEMO_MODE, no hard sell |

## Music / SFX

- Bed: warm acoustic / soft piano underscore, low dynamics; no thriller stings.
- SFX: soft UI click/tap on Check & Hang up; short success chime on risk label + test pass (quiet).
- Avoid: sirens, glitch, horror phone rings.

## Palette (locked)

- Paper `#F3F5F2` · Shield `#0A4D8C` · Danger `#9B1C1C` · Ink `#14201A`
- Type: Source Serif 4 (titles) · Atkinson Hyperlegible (UI/captions)

## On-screen claim rules

- **Sourced:** FTC 2024 — among older adults with ≥$10k business/gov imposter losses, **41%** phone as first contact (Imposter Data Spotlight Aug 2025 PDF).
- **Product copy only:** “Likely a scam”, Action Fraud `0300 123 2040`, Home lead lines.
- **Do not invent:** aggregate $ loss totals, extra hotlines, accuracy %.
- **CHI ROLESafe:** cut from this cut (no public DOI in research).

## Capture plan

Prefer `assets/captures/*.png` + `ui-session.webm`; fallback `docs/screenshots/`. Still need a short terminal/CI pass clip for the tests beat (`make check` / pytest + vitest) if not already in `ui-session.webm`.

## Build note

Remotion compositions mirror scenes 1:1; animate with `useCurrentFrame` + `interpolate`. Hold captions while readable. Wait for human storyboard approval before build.
