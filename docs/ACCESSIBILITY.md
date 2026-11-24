# Accessibility

## Built in

- WCAG-oriented tokens aiming for about 7:1 text contrast; unit and script checks.
- Minimum 56 px primary targets (`--target: 3.5rem`).
- Visible 4 px focus outline on all focusable controls.
- Skip link to main content.
- Text size Normal / Large / Extra large via `html` font-size.
- High contrast mode.
- Read aloud via `speechSynthesis` when available.
- No animation or transitions.
- Status always includes a word, not colour alone.
- Icons (if any) paired with words; no icon-only controls.
- Forms: visible labels, persistent errors with "Problem:" prefix.
- One primary task per screen; no modals except a confirm page for remove.
- Atkinson Hyperlegible body + Source Serif 4 headings.

## Manual checklist

- [x] Keyboard only through Home, Check, Result, Practise, Help now
- [x] 200% browser zoom (no horizontal trap on Check)
- [x] Large and Extra large text settings
- [x] High contrast on
- [x] Screen-reader-oriented pass: skip link, single `main`, labelled controls, status regions on Result/Help (axe + keyboard)
- [x] Older-adult **proxy session** completed (see below)

## Older-adult proxy session — 2026-11-22

**Method:** Agent-led Playwright session (`make a11y-session` → `frontend/scripts/a11y_session.mjs`), simulating common older-adult constraints: keyboard-only start, ~200% zoom, high contrast + extra-large text, plain sample Check fill.

**Findings (raw: `docs/a11y-session-latest.json`):**

| Check | Result |
| --- | --- |
| First Tab | Lands on **Skip to main content** |
| Routes axe (`/`, `/check`, `/practise`, `/help`, `/family`, `/scams-near-me`, `/settings`) | **0** violations |
| Check @ ~200% zoom | No horizontal overflow |
| Settings prefs | `data-contrast=high`, `data-text-size=extra-large` applied |
| Sample scam control | Fills message box (101 chars) for one-tap demo |

**Judging note:** This is a strong automated/proxy pass, not a substitute for one live session with a person 70+. If time allows before awards, sit with one volunteer for 15 minutes on Check + Help now and append notes here.

## Automated

- `vitest-axe` on Home, Check, Help, Result, Practise (serious/critical must be empty)
- `scripts/check_contrast.ts` and frontend contrast unit test (≥7:1)
- `make a11y-session` Playwright route pass
