# US-13 Demo Video — Draft Script

Target length: **~4:30**. Everything here is cuttable except the two
round-trips — those are the only thing `US-13`'s acceptance criteria
actually require ("video clearly shows two real round-trips, tagged by
provider, not just the pytest suite running").

Record with everything already running (gateway via `uv run glc serve`,
ngrok, both consoles' webhooks already registered against the current
tunnel's `/v1/channels/whatsapp/webhook` URL, phone already paired) —
don't show setup/boot time on camera. This script assumes that state.
Full setup steps (pairing, webhook registration, env vars) live in
`E2E-Testing.md` / `docs/E2E_TESTING.md` — not narrated here.

**Leads with Approach 3** (the gateway's own `/v1/channels/{name}/webhook`
route) rather than the standalone `demo_webhook_server.py` script, since
it's the correct long-term solution and exercises the full gateway
pipeline (allowlist, rate-limit, audit) rather than bypassing it. See
`INBOUND_WEBHOOK_ARCHITECTURE.md` for the full comparison.

---

### 0:00–0:20 — Intro (talking head or voiceover over a title card)

> "Hi, this is the WhatsApp channel adapter for GLC v1 — Group WhatsApp,
> slot `whatsapp`. This adapter speaks two upstream providers: Meta's
> Cloud API and Twilio's Sandbox API. I'll show a real message round-trip
> through each one, received directly by the GLC gateway."

### 0:20–0:40 — One-screen architecture (static diagram or terminal, no narration needed beyond this line)

> "A message comes in as a signed webhook to the gateway, the adapter
> verifies the signature, classifies trust, and the gateway's allowlist,
> rate-limiter, and audit log all run before the reply goes back out
> through whichever provider the message came in on."

*(Show the Mermaid diagram from `help_docs/whatsapp_adapter_flow.mermaid`
or just cut straight to the terminal — whichever is faster to set up.)*

### 0:40–1:05 — Show the running gateway and registered webhooks

*(Screen: terminal showing `uv run glc serve` up on port 8111, and a
second terminal or browser tab showing `ngrok http 8111`'s forwarding
URL.)*

> "The gateway's running with the new webhook route wired in, and ngrok's
> tunneling it out. My phone's already paired as the owner, so I can go
> straight to sending messages — full pairing and setup steps are in
> `E2E_TESTING.md` if you want to reproduce this."

*(Quick cut: show the registered Callback URL in the Meta app console and
the Twilio Sandbox "when a message comes in" field, both pointed at
`https://<ngrok-url>/v1/channels/whatsapp/webhook`.)*

> "Same URL, registered in both consoles — the route tells Meta and
> Twilio apart by their signature headers, not the path."

### 1:05–2:20 — Meta round-trip

*(Screen: phone WhatsApp chat with the Meta test number, split/picture-in-
picture with the terminal if possible.)*

1. Type and send a message from the phone, e.g. `"Hello from the Meta test!"`.
2. Cut to terminal — point at the request landing:
   ```
   INFO: ... "POST /v1/channels/whatsapp/webhook HTTP/1.1" 200 OK
   ```
3. Cut back to phone — show the `[glc echo] Hello from the Meta test!`
   reply arriving. This is the primary proof of the round-trip.

> "That's a real message, verified with Meta's HMAC-SHA256 signature,
> parsed into our typed envelope, passed through the gateway's allowlist
> and audit log, and echoed back through the real Graph API — not a mock."

### 2:20–3:35 — Twilio round-trip

*(Same shape, different number — the Twilio sandbox number.)*

1. Send a message from the phone to the sandbox number, e.g. `"Hello from Twilio!"`.
2. Cut to terminal, same generic `200 OK` line.
3. Cut back to phone — show the reply arriving via the sandbox number.
   Different number, different chat thread — visually distinct proof
   it's a separate provider from the Meta round-trip.

> "Same route, same code path, different signature scheme — Twilio signs
> with HMAC-SHA1 over the full webhook URL, not the raw body like Meta.
> Both providers are live and working from the same running gateway
> process."

### 3:35–3:55 — Fallback path, mentioned not demoed

> "One more thing: the gateway route lives in shared code outside our
> owned path, so it needs a separate review before it merges. In case
> that doesn't land in time, we've also built a standalone script —
> `demo_webhook_server.py` — that calls the same adapter directly and
> works today without any shared-code changes. Same two round-trips,
> just without the gateway's allowlist and audit pipeline in front."

### 3:55–4:15 — Automated coverage (fast, one screen, no line-by-line narration)

*(Screen: run `uv run pytest tests/channels/test_whatsapp.py glc/channels/catalogue/whatsapp/tests/ -v` — or show a pre-captured green run to save time — plus a glance at `ruff`/`mypy` passing.)*

> "Beyond the two providers you just saw live, there's automated
> regression coverage too — the 7 fixed Meta tests, plus 31 tests we
> built ourselves for the Twilio path, since the fixed suite can't
> exercise Twilio at all. All green, lint and type-checks clean."

### 4:15–4:30 — Wrap-up

> "One more thing worth calling out: the adapter caches which provider
> each contact last messaged from, so replies automatically go back
> through the right one — no manual switching. That's the whole
> round-trip for both providers, received natively by the gateway.
> Thanks for watching."

---

## Cut list if you need to go shorter (target ~3:00)

Cut, in this order, until you hit your target length:
1. The automated-coverage segment (3:55–4:15) — mention it in one sentence during the wrap-up instead.
2. The fallback-path mention (3:35–3:55) — cover it in one sentence in the wrap-up instead, or the PR description.
3. The architecture explanation (0:20–0:40) — the round-trips speak for themselves.
4. The provider-cache callout in the wrap-up — replace with just "thanks for watching."

**Never cut:** the two live round-trips themselves, or the phone showing
the `[glc echo] ...` reply arriving for each provider — that's the
primary evidence the rubric requires. Since the gateway route doesn't
print a per-message terminal log line (unlike the old demo-server
script), the phone's reply — arriving on a distinct number/chat thread
per provider — plus the narration naming the provider is what carries
that requirement here.

## Recording checklist before you hit record

- [ ] Gateway (`uv run glc serve`) and ngrok already running, tunnel pointed at port 8111
- [ ] Both webhooks (Meta + Twilio) already registered against the current tunnel's `/v1/channels/whatsapp/webhook` URL
- [ ] Phone already paired (`owner_paired`) — confirmed via a throwaway test message beforehand
- [ ] `TWILIO_WEBHOOK_URL` in `.env` matches the registered URL exactly, including trailing slash if Twilio signs with one (see `E2E-Testing.md` step 8b) — test this once before recording, not during
- [ ] `channels.yaml` has `whatsapp: {enabled: true}` on this branch — confirm before recording, since a disabled channel silently drops messages with no reply
- [ ] Screen recording captures both the phone (mirroring/PIP) and the terminal simultaneously, or plan clean cuts between them
- [ ] Decide upload target (YouTube unlisted / Loom / Vimeo) before recording, so the link is ready for the PR description immediately after
