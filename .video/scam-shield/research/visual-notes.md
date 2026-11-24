# Visual notes — scam-shield

Format: **explainer + app-demo**. Tone: civic trust leaflet — calm, plain, never shaming.

## Palette (from `frontend/src/styles/tokens.css`)

| Token | Hex | Role on screen |
| --- | --- | --- |
| `--paper` | `#F3F5F2` | Full-bleed app background |
| `--ink` | `#14201A` | Body text |
| `--ink-muted` | `#2A3A32` | Secondary / hints |
| `--primary` / `--shield` | `#0A4D8C` | Brand bar, logo wordmark, primary CTAs |
| `--on-primary` | `#FFFFFF` | Text on primary buttons |
| `--danger` | `#9B1C1C` | “I need help now” / urgent CTAs |
| `--success` | `#145A32` | Positive / debrief praise (use sparingly) |
| `--warn-bg` / `--warn-ink` | `#FFF4CC` / `#3D2E00` | Practice banner (“This is pretend…”) |
| `--highlight` | `#FFE066` | Marked scam phrases on Check result |
| `--panel` | `#FFFFFF` | Form panels / step cards |
| `--border` | `#3A4550` | Hairline rules, button outlines |

High-contrast mode flips to near-black/white + `#0000CC` primary — optional B-roll only if Settings is shown.

## Typography

- **Body / UI:** Atkinson Hyperlegible (400/700) — buttons, hints, steps.
- **Display / brand / page titles:** Source Serif 4 (600/700) — “Scam Shield”, “Is something worrying you?”, section titles.
- Base size ~1.25rem, line-height ~1.65; primary targets **3.5rem (56 px)**; radius **4 px** (not pill-heavy).

## UI chrome (from screenshots)

- **Header:** blue vertical brand bar + “Scam Shield” serif; red **I need help now**; outlined **Text size and contrast**; “Back to start” text link.
- **Home:** brand repeated in hero; one column of full-width buttons with short captions under each; footer disclaimer.
- **Check:** white bordered panel; photo file picker (OCR path) above message textarea; blue **Check this message**.
- **Practise setup:** scenario / difficulty / mode selects; blue **Start practice** (demo path: Fake bank fraud call → Easy → Be the target).
- **Help now:** numbered white step cards; **Who to contact** list including Action Fraud **0300 123 2040**.
- **Family / Scams:** secondary screens — optional late cut; Scams bars labelled not verified.

## Motion / pacing language (explainer + demo)

1. **Open (problem, ~8–12s):** still or slow push on paper background + FTC-sourced line (phone first contact / payment mix). No shame framing. End on tone line: “Scammers are professionals. Stopping is always a good move.”
2. **Brand land (~3–5s):** hard cut or dissolve to live Home at `127.0.0.1:5173` — brand first, then large buttons.
3. **Check money shot (~12–18s):** paste sample or upload `docs/samples/scammer-message.png` → waiting “Checking…” → result with yellow phrase highlights + risk label.
4. **Practise (~10–15s):** yellow pretend banner visible; one reply; **Hang up and see how I did**; debrief praise-first.
5. **Help now (~6–10s):** numbered steps + Action Fraud number on screen (do not invent other hotlines).
6. **Close (~4–6s):** DEMO_MODE / clone-and-run or tagline card; optional Family/Scams flash if time.

Avoid: dark neon cyber aesthetics, purple AI gradients, emoji stickers, floating “AI powered” badges over the UI.

## Competitor motion cues (medium)

- Public-service scam PSAs: slow VO, hold on phone/number, single calm CTA — match Help-now pacing.
- “Hang up and call the number on your card” bank spots: problem → interrupt → trusted channel — mirror Check → Help arc.
