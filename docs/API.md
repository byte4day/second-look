# API reference

OpenAPI interactive docs: `http://localhost:8000/docs`

Errors use `{ "error": { "code": "...", "message_plain": "..." } }`.

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/health` | Liveness |
| GET | `/api/health/groq` | Model check status |
| POST | `/api/auth/request-code` | Email a 6-digit code |
| POST | `/api/auth/verify-code` | Exchange code for JWT |
| GET | `/api/me` | Current user |
| DELETE | `/api/me` | Delete account and linked data |
| GET | `/api/scenarios` | Practice scenarios |
| POST | `/api/drills` | Start a drill |
| POST | `/api/drills/{id}/turns` | Send a user turn |
| POST | `/api/drills/{id}/finish` | Debrief |
| POST | `/api/analyze/text` | Check pasted text |
| POST | `/api/analyze/image` | Check a photo (base64) |
| POST | `/api/voice/transcribe` | Whisper STT |
| GET/POST/DELETE | `/api/family` | Contacts (auth) |
| POST | `/api/family/invitations/{token}/accept` | Accept invite |
| POST | `/api/alerts` | Send family alert |
| POST | `/api/alerts/test` | Test alert |
| GET | `/api/push/vapid-key` | Optional Web Push |
| POST | `/api/push/subscribe` | Store push subscription |
| POST | `/api/reports` | Anonymous report |
| GET | `/api/reports/summary?area=` | Weekly area summary |
| GET | `/api/content/help-now?region=` | Help now pack |

## Curl examples

```bash
curl -s -X POST http://localhost:8000/api/analyze/text \
  -H 'Content-Type: application/json' \
  -d '{"text":"This is Metro Trust Bank Fraud Unit. Share the one-time code."}'

curl -s -X POST http://localhost:8000/api/drills \
  -H 'Content-Type: application/json' \
  -d '{"scenario_id":"bank_otp","difficulty":"easy","mode":"experience"}'
```
