# Gaps — scam-shield

Anything that might appear on screen without a primary source must be labelled **illustrative**.

## Must not invent on screen

- **Dollar loss totals** (e.g. “$X billion lost,” “$700 million”) — **not** in README; not verified from the FTC PDF body for VO use. Prefer sourced figures only: 41% phone first contact; crypto 33% / bank 20% / cash 16%; report counts 1,790→8,269 (2020–2024). Mark any other loss headline **illustrative** or cut it.
- **Hotlines other than** Action Fraud `0300 123 2040`, Police Scotland `101`, or FTC ReportFraud (generic pack) — do not invent numbers. (source: README TODO + region JSON)
- **“Guaranteed detection” / accuracy %** — risk labels are a guide, not a guarantee. (source: SAFETY.md)

## Unverified / incomplete sources

- **CHI 2026 ROLESafe** (144 older adults, Experiencer/Helper/Observer) — only via README; no DOI/URL in-repo. On-screen claim should be soft (“research suggests practice helps”) or cut; do not invent study stats beyond README wording.
- **FTC hub URL** in README (`…/data-spotlight`) returned **404** at research time — use the August 2025 Imposter Data Spotlight PDF URL for citations/cards.
- README “Final build report” said screenshot PNGs not committed; **screenshots are now present** under `docs/screenshots/` — inventory updated. Older-adult **live** user test still may lag proxy a11y session (see ACCESSIBILITY.md).

## Capture gaps for film

- No still of **Check result** (highlights + risk label) in `docs/screenshots/` — **need live capture**.
- No still of **Practise chat / debrief** — **need live capture**.
- Brief requires **real automated tests** on camera — no packaged clip yet.
- Standalone **logo** asset beyond in-app wordmark — crop or export.
- **Help now** screenshot crop may cut off Action Fraud row — confirm full contact list on live `:5173` before VO over number.

## Illustrative-only (if used)

- Generic “concerned older adult on phone” stock B-roll — **illustrative**; prefer real app UI.
- Competitor PSA pacing references — **illustrative** motion language, not Scam Shield product proof.
- Map pins / area bars on Scams near me — seeded demo data; label **not verified** if shown (matches product copy).

## Open questions for storyboard (not facts)

- Exact VO wording for FTC 41% line (keep footnote-accurate).
- Whether Family / Scams appear in 45–60s cut (demo script says optional).
- Whether to show Groq live path or stick to `DEMO_MODE` only (safer for judges / film reliability).
