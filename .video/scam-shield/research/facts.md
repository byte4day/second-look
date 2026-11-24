# Facts — scam-shield

Depth: **medium** · Format: **explainer + app-demo** · Slug: `scam-shield`

## Product identity

- Scam Shield is a calm web app that helps older adults practise hanging up on pretence scammers, check worrying messages, and reach trusted people quickly; built for a student social-impact hackathon and people who are not tech experts. (source: `/home/byte/hackathon/README.md`)
- Devpost tagline: “Practise hanging up. Check a message. Tell someone you trust.” (source: `/home/byte/hackathon/README.md`)
- Licence: MIT; built for Code for Change / Devpost. (source: `/home/byte/hackathon/README.md`)
- Backend app version reported by FastAPI/health is **0.4.0**. (source: `/home/byte/hackathon/backend/app/main.py`; `/home/byte/hackathon/backend/app/api/routers/health.py`)
- Stack: React (Vite) frontend → FastAPI → LLM gateway (Groq or DEMO fixtures) → SQLite/Postgres; optional email (console/SMTP/Resend). (source: `/home/byte/hackathon/README.md`; `/home/byte/hackathon/docs/ARCHITECTURE.md`)
- Judges can run a full demo in under ten minutes with or without an API key; `DEMO_MODE=true` is the default. (source: `/home/byte/hackathon/README.md`)
- Local demo URLs in README: frontend `http://localhost:5173`, API `http://localhost:8000`. Film brief uses live app at `http://127.0.0.1:5173`. (source: `/home/byte/hackathon/README.md`; `/home/byte/hackathon/.video/scam-shield/brief.md`)

## Problem (sourced loss / contact stats only)

- Imposter scams (bank, government, grandchild, tech support, romance) cause high losses for older adults; common red flags include unexpected contact, urgency, secrecy, threats, requests for one-time codes, and unusual payment methods. (source: `/home/byte/hackathon/README.md`)
- FTC Imposter Data Spotlight (Aug 2025), footnote 4: In **2024**, **41%** of older adults who reported losing **$10,000 or more** to a business or government imposter scam indicated a **phone call** was the initial contact method; **15%** online ad or pop-up; **13%** email. (source: `https://search.ftc.gov/system/files/ftc_gov/pdf/Imposter-Data-Spotlight-August-2025.pdf`; also summarized in `/home/byte/hackathon/README.md`)
- Same spotlight, footnote 5: Among those high-loss older-adult reports in **2024**, payment methods included **cryptocurrency 33%**, **bank transfer 20%**, and **cash 16%**. (source: `https://search.ftc.gov/system/files/ftc_gov/pdf/Imposter-Data-Spotlight-August-2025.pdf`; also summarized in `/home/byte/hackathon/README.md`)
- Same spotlight, footnote 3: Number of business/government imposter reports from older adults with loss ≥ $10K: **1,790 (2020)** → **8,269 (2024)** (more than fourfold). (source: `https://search.ftc.gov/system/files/ftc_gov/pdf/Imposter-Data-Spotlight-August-2025.pdf`)
- Same spotlight: for losses over **$100,000**, report counts rose nearly **sevenfold** (2020–2024) and combined reported losses **eightfold**. (source: `https://search.ftc.gov/system/files/ftc_gov/pdf/Imposter-Data-Spotlight-August-2025.pdf`)
- Tone rule for the product/video: never shame; scammers are professionals; stopping is always a good move. (source: `/home/byte/hackathon/README.md`; `/home/byte/hackathon/.video/scam-shield/brief.md`)

## Why simulation (research cited in README)

- A CHI 2026 study (ROLESafe, 144 older adults) found practising as the target (“Experiencer”) and advising a simulated victim (“Helper”) both improved fraud identification versus static material; Helpers beat passive Observers; group differences were **not** seen at follow-up — so the app includes both modes and an optional “remind me to practise” refresher. (source: `/home/byte/hackathon/README.md` — no public DOI/URL linked in-repo)

## Live app features (demo surface)

1. **Check a message (OCR / photo)** — paste text or photograph a letter/photo; words can be copied into the box; risk label, highlights, next steps. UI: “Check a message or letter”; photo field “Take or choose a photo”; status “Reading the words from your photo…”. (source: `/home/byte/hackathon/README.md`; `/home/byte/hackathon/frontend/src/strings.ts`; `/home/byte/hackathon/docs/screenshots/check.png`)
2. **Practise drills** — pretend scammer chat (optional voice), scenario/difficulty/mode (Be the target / Help the victim), hang up → debrief with marked moments; yellow practice banner: “This is pretend…”. (source: `/home/byte/hackathon/README.md`; `/home/byte/hackathon/frontend/src/strings.ts`; `/home/byte/hackathon/docs/screenshots/practise.png`)
3. **Help now** — calm numbered steps for “I think I am being scammed right now”; always-visible header CTA “I need help now”. Default UK region pack includes **Action Fraud** phone **0300 123 2040** (England, Wales, Northern Ireland) and Action Fraud URL. (source: `/home/byte/hackathon/README.md`; `/home/byte/hackathon/backend/app/data/regions/uk-example.json`; `/home/byte/hackathon/docs/screenshots/help.png`)
4. **My family** — trusted contacts with invitation consent, email alerts, and share-link fallback (SMS/WhatsApp share without signing in noted in demo script). (source: `/home/byte/hackathon/README.md`; `/home/byte/hackathon/docs/DEMO_SCRIPT.md`; `/home/byte/hackathon/docs/screenshots/family.png`)
5. **Scams near me** — anonymous reports and a simple weekly area summary; reports labelled unverified / “reported by users, not verified”. (source: `/home/byte/hackathon/README.md`; `/home/byte/hackathon/docs/SAFETY.md`; `/home/byte/hackathon/docs/screenshots/scams.png`)

## Home / UX copy (on-screen)

- Home brand + headline: “Scam Shield” / “Is something worrying you?”; lead: “Choose one thing. Take your time. Stopping is always a good move.” (source: `/home/byte/hackathon/frontend/src/strings.ts`; `/home/byte/hackathon/docs/screenshots/home.png`)
- Promise: “Plain words. Large buttons. Built for people who are not tech experts.” (source: `/home/byte/hackathon/frontend/src/strings.ts`)
- Accessibility controls: text size, high contrast, read aloud; design targets AAA-oriented contrast and **56 px** targets; fonts Atkinson Hyperlegible + Source Serif 4. (source: `/home/byte/hackathon/README.md`; `/home/byte/hackathon/docs/ACCESSIBILITY.md`; `/home/byte/hackathon/frontend/src/styles/tokens.css`)
- Risk labels are a guide, not a guarantee; not legal or financial advice. (source: `/home/byte/hackathon/docs/SAFETY.md`; `/home/byte/hackathon/README.md`)

## Demo / film constraints

- Demo script (~90s) beats: Check → Practise → Help now; Family and Scams near me optional. (source: `/home/byte/hackathon/docs/DEMO_SCRIPT.md`)
- Film brief: ~45–60s, 16:9; problem first then solution; must show real website at localhost:5173, real Check/Practise/Help flows, real automated tests; audience = hackathon judges. (source: `/home/byte/hackathon/.video/scam-shield/brief.md`)
- No account needed for Practise, Check, Help now, or reading summaries; account (email code) needed for family contacts and push. (source: `/home/byte/hackathon/README.md`)

## Safety (on-screen / ethics)

- Scammer persona uses fictional organisation names; replies capped and scrubbed; real secrets replaced with `[hidden]`. (source: `/home/byte/hackathon/docs/SAFETY.md`)
- Family alerts require double opt-in; rate limit 3 alerts/hour/account. (source: `/home/byte/hackathon/docs/SAFETY.md`)
