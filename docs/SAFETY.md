# Safety and privacy

## Scammer persona guardrails

- Only fictional organisation names from the scenario files are used.
- Model replies are capped at 60 words and scrubbed of real-looking URLs and phone numbers.
- Real card numbers (Luhn), password phrases, and similar secrets typed by the user are replaced with `[hidden]` and never sent to the model.
- Requests to write scam scripts or bypass bank controls end the drill with a short refusal.
- Debriefs praise hanging up and focus on spotting tricks, not improving fraud.

## Family alerts

- Contacts require double opt-in via an invitation token.
- Alerts are only sent to contacts with status `accepted`.
- Alert emails include an unsubscribe token.
- Rate limit: 3 alerts per hour per account.
- Message details are optional; default content is minimal.

## Local storage trade-off

The frontend stores the JWT in `localStorage` for passwordless sign-in. That is convenient for a demo, but any script running on the origin can read it. Prefer a short-lived token and "Delete all my data" before sharing a device.

## Risk scores

Analyzer output is a guide, not a guarantee. Always contact your bank or the sender using a number you already know. This app is not legal or financial advice.

## Reports

Community reports are anonymous, scrubbed, and labelled "reported by users, not verified". Areas under `MIN_REPORTS_TO_SHOW` are hidden.
