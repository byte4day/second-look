# Accessibility

## Built in

- WCAG-oriented tokens aiming for about 7:1 text contrast; unit and script checks.
- Minimum 56 px primary targets (`--target: 3.5rem`).
- Visible 4 px focus outline on all focusable controls.
- Skip link to main content.
- Text size Normal / Large / Extra large (20 / 24 / 28 px) via `html` font-size.
- High contrast mode.
- Read aloud via `speechSynthesis` when available.
- No animation or transitions.
- Status always includes a word, not colour alone.
- Icons (if any) paired with words; no icon-only controls.
- Forms: visible labels, persistent errors with "Problem:" prefix.
- One primary task per screen; no modals except a confirm page for remove.

## Manual checklist

- [ ] Keyboard only through Home, Check, Result, Practise, Help now
- [ ] 200% browser zoom
- [ ] Large and Extra large text settings
- [ ] High contrast on
- [ ] Screen reader on Home, Result, and Practise
- [ ] Older-adult test: **not yet completed** — note date and findings here after the session

## Automated

- `vitest-axe` on Home
- `scripts/check_contrast.ts` and frontend contrast unit test
