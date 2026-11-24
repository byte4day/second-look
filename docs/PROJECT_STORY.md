# Second Look

**Every scam falls apart on a second look.**

## Inspiration

Scammers don't win because their targets are foolish. They win because they're professionals working on someone who is rushed, scared or alone. For older adults the damage is huge. FTC data for 2024 shows that among older adults who lost $10,000 or more to business or government imposters, 41% said a phone call was the first contact. They paid by crypto (33%), bank transfer (20%) and cash (16%).

Most scam advice is a leaflet: a list of red flags you read once and forget. A CHI 2026 study (ROLESafe, 144 older adults) found that *practising* against a simulated scammer, or *advising* a simulated victim, improved fraud spotting more than reading static material. So we built something people can practise with, not just read.

Our rule from day one: **never shame**. Stopping is always a good move.

## What it does

Second Look is a calm web app with five numbered choices, so a family member can say "press number 1" over the phone:

1. **Check a message**: paste a text or snap a photo of a letter. The app marks the exact words that are red flags (a fake "account locked" alert, a request for a code, a 30-minute deadline). It then gives a risk level and plain next steps.
2. **Practise**: a pretend scammer "calls" and pushes urgency, secrecy and code requests, by text or by voice. When you hang up, a debrief shows every trick you spotted.
3. **I need help now**: five calm steps and real helplines for when it's happening right now, with a read-aloud button.
4. **My family**: trusted people get a short alert when you ask for help. They accept an invite first, and there's a text or WhatsApp fallback with no account.
5. **Scams near me**: anonymous reports from your area, so neighbours know what's going round this week.

**Bit**, our pixel-shield mascot, guides each step with one plain sentence. Bit looks happy, calm, worried or thinking depending on what it finds.

## How we built it

- **Frontend:** React + Vite. Large type in Atkinson Hyperlegible, 56px tap targets, a high-contrast mode, text sizes up to 140%, and screen-reader focus on each new page.
- **Backend:** FastAPI with SQLite or Postgres. Sign-in is a passwordless email code, and family contacts use double opt-in.
- **AI: the Unorouter API.** One gateway module talks to Unorouter's OpenAI-compatible endpoint for message analysis, the scammer role-play, debriefs and speech-to-text. It handles retries, model fallback and structured JSON output. Groq is kept only as a backup provider.
- **Photo check:** local OCR (RapidOCR) reads the letter on the server first. The words then go through the same text checker, so photos work even without a vision model.
- **A safety layer that doesn't trust the model:**
  - Every quote the AI marks must appear word for word in the original message, or it's dropped.
  - A local rule engine runs on every message and can only *raise* the risk, never lower it.
  - Advice comes from fixed, reviewed lists, not free model text.
  - Text that tries to instruct the AI ("ignore previous instructions") is flagged as a red flag rather than obeyed.
  - Real numbers, links and codes are stripped from anything people type in practice.
- **DEMO_MODE:** the full app runs offline with no API key, using the same local rules. Judges can try it in five minutes.

## Challenges we ran into

- **A checker that says "probably fine" is dangerous.** Our first version called any message with no keyword matches safe, so "Hi Mum, new number, send £300 for rent" slipped through. Now "no match" means "we cannot tell", and only short everyday messages count as fine.
- **Scam text attacking the AI.** A scam containing "ignore previous instructions" once made the checker refuse to answer. Now that wording counts against the message.
- **Highlights that cut words in half.** The marked phrases sometimes stopped mid-word ("YE|S"), and overlapping reasons lost their numbers. We now widen every quote to whole words and keep every reason's number.
- **Designing for older users without talking down to them.** We wrote plain words, one action per screen, and never "Uh oh".

## Accomplishments that we're proud of

- 69 backend and 18 frontend tests, plus an automated accessibility check with **0 axe issues across 7 pages** and a 25-prompt safety evaluation.
- A security pass that fixed real issues before anyone shipped them:
  - sign-in code brute force
  - path traversal
  - injection into a command-line option
  - oversized image uploads
  - rate-limit and error responses that browsers blocked for missing CORS headers
- A 50-second explainer film made from the real running app, narrated by Bit.

## What we learned

- Users should never have to trust the model blindly. Exact-quote checks and rules that can only raise the risk make the AI useful without letting it be wrong in the dangerous direction.
- Older adults don't need a simpler app so much as a *calmer* one: one choice, one sentence, one next step.

## What's next

- A test with older adults at a local community centre.
- Region packs with verified helplines beyond the UK.
- A "remind me to practise" refresher, because the study found the benefit fades without repetition.
- More languages, starting with Urdu and Polish.

## Built with

Unorouter API, FastAPI, Python, React, TypeScript, Vite, SQLite, RapidOCR, edge-tts, Playwright, vitest, pytest, axe-core
