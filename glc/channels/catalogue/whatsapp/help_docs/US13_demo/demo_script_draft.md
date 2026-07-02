# US-13 Demo Video — Draft Script

Target length: **~4:30**. Everything here is cuttable except the two
round-trips — those are the only thing `US-13`'s acceptance criteria
actually require ("video clearly shows two real round-trips, tagged by
provider, not just the pytest suite running").

Record with everything already running (gateway, `demo_webhook_server.py`,
ngrok, both consoles' webhooks already registered, phone already paired)
— don't show setup/boot time on camera. This script assumes that state.

---

### 0:00–0:20 — Intro (talking head or voiceover over a title card)

> "Hi, this is the WhatsApp channel adapter for GLC v1 — Group WhatsApp,
> slot `whatsapp`. This adapter speaks two upstream providers: Meta's
> Cloud API and Twilio's Sandbox API. I'll show a real message round-trip
> through each one."

### 0:20–0:40 — One-screen architecture (static diagram or terminal, no narration needed beyond this line)

> "A message comes in as a signed webhook, the adapter verifies the
> signature, classifies trust, and hands a typed envelope to the agent.
> The agent's reply goes back out through whichever provider the message
> came in on."

*(Show the Mermaid diagram from `help_docs/whatsapp_adapter_flow.mermaid`
or just cut straight to the terminal — whichever is faster to set up.)*

### 0:40–0:55 — Show the running processes (fast cut, no dead air)

> "Here's the adapter's demo server already running, listening for both
> providers on one tunnel."

*(Quick screen glance: terminal showing `[demo] Approach 2 (US-13) server
listening on port 8111`. Do not narrate the pairing steps — say only:)*

> "My phone's already paired as the owner, so I can go straight to
> sending messages."

### 0:55–2:10 — Meta round-trip

*(Screen: phone WhatsApp chat with the Meta test number, split/picture-in-
picture with the terminal if possible.)*

1. Type and send a message from the phone, e.g. `"Hello from the Meta test!"`.
2. Cut to terminal — point at the log line as it appears:
   ```
   [demo] inbound provider=meta from=<wa_id> trust=owner_paired text='Hello from the Meta test!'
   [demo] send() result: {'messaging_product': 'whatsapp', ...}
   ```
3. Cut back to phone — show the `[glc echo] Hello from the Meta test!` reply arriving.

> "That's a real message, verified with Meta's HMAC-SHA256 signature,
> parsed into our typed envelope, and echoed back through the real Graph
> API — not a mock."

### 2:10–3:25 — Twilio round-trip

*(Same shape, different number — the Twilio sandbox number.)*

1. Send a message from the phone to the sandbox number, e.g. `"Hello from Twilio!"`.
2. Cut to terminal:
   ```
   [demo] inbound provider=twilio from=<wa_id> trust=owner_paired text='Hello from Twilio!'
   [demo] send() result: {'sid': ..., 'status': 'queued', ...}
   ```
3. Cut back to phone — show the reply arriving via the sandbox number.

> "Same adapter, same code path, different signature scheme — Twilio
> signs with HMAC-SHA1 over the full webhook URL, not the raw body like
> Meta. Both providers are live and working from the same running
> process."

### 3:25–3:50 — Automated coverage (fast, one screen, no line-by-line narration)

*(Screen: run `uv run pytest tests/channels/test_whatsapp.py glc/channels/catalogue/whatsapp/tests/ -v` — or show a pre-captured green run to save time — plus a glance at `ruff`/`mypy` passing.)*

> "Beyond the two providers you just saw live, there's automated
> regression coverage too — the 7 fixed Meta tests, plus 31 tests we
> built ourselves for the Twilio path, since the fixed suite can't
> exercise Twilio at all. All green, lint and type-checks clean."

### 3:50–4:20 — Wrap-up

> "One more thing worth calling out: the adapter caches which provider
> each contact last messaged from, so replies automatically go back
> through the right one — no manual switching. That's the whole
> round-trip for both providers. Thanks for watching."

---

## Cut list if you need to go shorter (target ~3:00)

Cut, in this order, until you hit your target length:
1. The automated-coverage segment (3:25–3:50) — mention it in one sentence during the wrap-up instead.
2. The architecture explanation (0:20–0:40) — the round-trips speak for themselves.
3. The provider-cache callout in the wrap-up — replace with just "thanks for watching."

**Never cut:** the two live round-trips themselves, or the moment each
terminal log line shows `provider=meta` / `provider=twilio` — that's the
one thing the rubric explicitly checks for.

## Recording checklist before you hit record

- [ ] Gateway, `demo_webhook_server.py`, and ngrok already running
- [ ] Both webhooks (Meta + Twilio) already registered against the current tunnel URL
- [ ] Phone already paired (`owner_paired`) — confirmed via a throwaway test message beforehand
- [ ] `TWILIO_WEBHOOK_URL` has the trailing slash (see `E2E-Testing.md` step 8b) — test this once before recording, not during
- [ ] Screen recording captures both the phone (mirroring/PIP) and the terminal simultaneously, or plan clean cuts between them
- [ ] Decide upload target (YouTube unlisted / Loom / Vimeo) before recording, so the link is ready for the PR description immediately after
