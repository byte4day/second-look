# Architecture decisions

## Frontend: Vite and React

The UI uses Vite with React 18+ and TypeScript in strict mode. Vite gives fast local development and a straightforward production build. React Router handles screen navigation without a full page reload. TanStack Query manages API loading and caching against the backend under `/api/...`.

## Plain CSS and design tokens

The interface uses hand-written CSS split into tokens, base, layout, and components. Tailwind and third-party UI kits were avoided so contrast, touch targets, and typography stay predictable for older adults. Colours and spacing live in `frontend/src/styles/tokens.css` and are checked by `scripts/check_contrast.ts` and Vitest.

## Optional map (Leaflet)

The Scams near me screen can show an OpenStreetMap view via `react-leaflet`. The map is lazy-loaded and hidden by default so the page works without map tiles or JavaScript map support. Reports do not depend on the map.

## PWA and offline help

`vite-plugin-pwa` registers a service worker. Help now content is cached with a network-first strategy so basic steps remain available when offline after a prior visit.

## Copy and accessibility

All user-facing strings are in `frontend/src/strings.ts` in plain British English. Persistent error banners use a Close control. Skip link and focus outlines follow WCAG-oriented patterns. Automated checks include `vitest-axe` on the home screen and contrast ratio tests on design tokens.

## Practice caller voice uses neural TTS

Caller lines are synthesized by `POST /api/voice/speak`. Order: Groq Orpheus (if terms accepted) → Microsoft neural voices via `edge-tts` (natural human speech with light phone EQ) → espeak last resort. Scammer persona uses `en-US-ChristopherNeural`. The browser plays the returned WAV.

## Photo Check uses local OCR as the primary vision path

As of 2026-11-22 this Groq account exposes **no** vision chat models (Scout/Maverick/legacy llama-vision unavailable). Photo Check therefore treats **RapidOCR → text analyzer** as the primary path, not a fallback:

1. Browser downscales the photo and POSTs `/api/analyze/ocr` to auto-fill the box.
2. Check submits the (editable) text to `/api/analyze/text`.
3. `/api/analyze/image` also OCRs then analyzes, for API clients.

If `GROQ_VISION_MODEL` is later set to a working multimodal ID, the image route still tries vision when OCR returns empty.

## DEMO_MODE analyze is input-aware

Offline demo mode no longer returns one fixed bank-scam JSON for every paste. It runs the same local heuristics used as the live fallback, so a normal lunch message stays “probably fine” and a Chase fraud SMS still flags as a scam. That keeps judge demos honest without a Groq key.

## Family invites use an app link

Invitation emails include `{PUBLIC_APP_URL}/invite/{token}` rather than a raw API POST instruction, so relatives can accept in the browser.

## Backend hardening (v0.4)

- SQLite uses WAL + busy timeout for multi-request demos.
- Global + LLM rate limits with `Retry-After`.
- LLM circuit breaker trips after repeated upstream failures.
- Analyzer refuses howto-scam **and** prompt-injection style text.
- Image uploads capped (~2.5M base64) and MIME-allowlisted.
- Health exposes dependency checks; `/api/health/ready` for containers.
- Security headers: `nosniff`, `DENY` framing, `no-referrer`.

## Unorouter as the primary AI provider (2026-11-24)

The Build Anything hackathon requires the Unorouter API. The LLM gateway now talks to Unorouter's OpenAI-compatible endpoint (`https://api.unorouter.com/v1`) through the `openai` SDK, and speech-to-text uses its hosted Whisper. `LLM_PROVIDER=auto` picks Unorouter whenever `UNOROUTER_API_KEY` is set and keeps Groq as a fallback, so existing Groq setups still work. Vision no longer silently falls back to a text-only model.

## Bit, the mascot (2026-11-24)

Bit is a 16×18 pixel-art shield drawn as inline SVG (`components/Bit.tsx`), with four moods (happy, calm, worried, thinking) that follow the risk level. Bit is decorative (`aria-hidden`); its speech bubble is real text. Motion (a slow bob and blink) only runs when the reader has not asked for reduced motion. Home choices and Result sections carry number tags so a family member can say "press number 1" over the phone.
