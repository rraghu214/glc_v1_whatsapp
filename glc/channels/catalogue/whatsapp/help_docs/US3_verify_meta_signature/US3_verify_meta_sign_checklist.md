# US-3: verify_meta_signature — Strategy & Checklist

**Branch:** `feature/us3-verify-meta-signature`
**File to change:** `glc/channels/catalogue/whatsapp/adapter.py`
**Depends on:** nothing (Wave 1, fully parallel)
**Feeds into:** US-9 (`on_message` orchestrator)

---

## Strategy

### What US-3 delivers

A single module-level helper function in `adapter.py`:

```python
def verify_meta_signature(raw_body: bytes, headers: dict) -> bool:
```

It is the **exact mirror** of `_sign()` in `tests/channels/mocks/whatsapp_mock.py` —
the mock signs webhooks with HMAC-SHA256; this function verifies them.

### Algorithm (HMAC-SHA256, Meta Cloud API)

```
1. secret   = os.environ.get("WHATSAPP_APP_SECRET", "")
2. sig      = headers.get("X-Hub-Signature-256", "")
3. If secret is empty OR sig does not start with "sha256=" → return False
4. expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
5. return   hmac.compare_digest(expected, sig.removeprefix("sha256="))
```

Three invariants that must hold:
- **Missing header** (`{}`) → False, no computation attempted
- **Wrong secret** (tampered) → False, compare_digest ensures constant time
- **Correct HMAC** → True

### Why constant-time comparison matters

`hmac.compare_digest` prevents timing attacks where an attacker could brute-force
the secret by measuring how quickly string comparison short-circuits. Using `==`
instead would be a security defect even though both produce the same boolean.

### Placement decision

`verify_meta_signature` lives as a **module-level function** in `adapter.py`, NOT
as a method on `Adapter`. Reasons:
- US-9's `on_message` calls it internally — no need for it to be public API on the class
- Pure function (no `self`) is directly unit-testable without instantiating the adapter
- HANDOFF §2.7 confirms helper names and placement are the team's choice

### What US-3 does NOT do

- Does NOT touch `on_message` or `send` — those are US-9 and US-10 respectively
- Does NOT parse the JSON body — that is US-4 (`parse_meta_payload`)
- Does NOT make pytest Test 7 pass on its own — Test 7 calls `on_message`, which is
  wired up in US-9. US-3's acceptance criteria are verified manually (see §4 below).

### How the mock and function interlock

```
whatsapp_mock.py                        adapter.py
────────────────                        ──────────
_sign(body, secret):
  hmac.new(secret, body, sha256)   ←→  verify_meta_signature(raw_body, headers):
  hexdigest()                            hmac.new(secret, raw_body, sha256)
                                         hexdigest()
                                         compare_digest(expected, from_header)

queue_signed_webhook()   →  (raw, {"X-Hub-Signature-256": "sha256=<hex>"})
queue_unsigned_webhook() →  (raw, {})
queue_tampered_webhook() →  (raw, {"X-Hub-Signature-256": "sha256=<wrong>"})
```

### How Test 7 will use this function (preview, implemented in US-9)

Test 7 passes `{"raw_body": raw, "headers": headers}` to `on_message`. US-9 will
detect this Shape B input and call `verify_meta_signature(raw, headers)`. If it
returns False → `on_message` returns None. If True → continue to parse + classify.

---

## Checklist

### Pre-flight

- [ ] Confirm active branch is `feature/us3-verify-meta-signature`
      (`git branch --show-current`)
- [ ] Confirm `WHATSAPP_APP_SECRET` is present in `.env`
      (set during US-1; value = `DEFAULT_APP_SECRET = "test-app-secret"` in the mock
      for local test runs; real value from Meta Developer Console for live tests)
- [ ] Re-read `_sign()` in [whatsapp_mock.py](../../../../../../../tests/channels/mocks/whatsapp_mock.py)
      (lines 86-87) — the function to implement is its exact inverse

### Implementation

- [ ] Open [adapter.py](../../../adapter.py)
- [ ] Add imports at the top (after `from __future__ import annotations`):
      `import hashlib`, `import hmac`, `import os`
- [ ] Add `verify_meta_signature` as a **module-level function** (before the `Adapter` class):
  ```python
  def verify_meta_signature(raw_body: bytes, headers: dict) -> bool:
      secret = os.environ.get("WHATSAPP_APP_SECRET", "")
      sig_header = headers.get("X-Hub-Signature-256", "")
      if not secret or not sig_header.startswith("sha256="):
          return False
      expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
      return hmac.compare_digest(expected, sig_header.removeprefix("sha256="))
  ```
- [ ] Verify the function signature exactly matches the HANDOFF §7.3 spec:
  - Parameter 1: `raw_body: bytes` (the raw, unparsed webhook body)
  - Parameter 2: `headers: dict` (the HTTP request headers dict)
  - Return: `bool`
- [ ] Do NOT modify `on_message` or `send` — those remain `NotImplementedError` stubs

### Manual verification (3 required cases per HANDOFF §7.3)

Run this one-liner in a terminal from the project root to confirm all 3 cases:

```bash
uv run python - <<'EOF'
import os, json
os.environ["WHATSAPP_APP_SECRET"] = "test-app-secret"

from glc.channels.catalogue.whatsapp.adapter import verify_meta_signature
import hmac, hashlib

body = b'{"object":"whatsapp_business_account"}'
secret = "test-app-secret"
correct_sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
wrong_sig   = "sha256=" + hmac.new(b"WRONG", body, hashlib.sha256).hexdigest()

# Case 1: Unsigned — no header
assert verify_meta_signature(body, {}) is False, "FAIL: unsigned must return False"
print("PASS  Case 1: unsigned → False")

# Case 2: Tampered — wrong secret
assert verify_meta_signature(body, {"X-Hub-Signature-256": wrong_sig}) is False, \
    "FAIL: tampered must return False"
print("PASS  Case 2: tampered → False")

# Case 3: Valid — correct HMAC
assert verify_meta_signature(body, {"X-Hub-Signature-256": correct_sig}) is True, \
    "FAIL: valid must return True"
print("PASS  Case 3: valid → True")

print("\nAll 3 manual cases passed.")
EOF
```

- [ ] Case 1 passes: unsigned webhook → `False`
- [ ] Case 2 passes: tampered webhook (wrong secret) → `False`
- [ ] Case 3 passes: correctly signed webhook → `True`

### Quality gates (required before mini-PR per US-12)

```bash
ruff check glc/channels/catalogue/whatsapp/
```
- [ ] `ruff` reports zero errors or warnings

```bash
mypy glc/channels/catalogue/whatsapp/
```
- [ ] `mypy` reports zero errors

```bash
uv run python scripts/check_pr_boundaries.py --base main --head HEAD --group "Group WhatsApp"
```
- [ ] Boundary check passes (only files under `glc/channels/catalogue/whatsapp/` changed)

### Commit

- [ ] Stage only the owned path:
  ```bash
  git add glc/channels/catalogue/whatsapp/adapter.py
  ```
- [ ] Confirm no other files are staged (`git status`)
- [ ] Commit:
  ```bash
  git commit -m "US-3: verify_meta_signature — HMAC-SHA256 over raw body, constant-time compare"
  ```
- [ ] Push:
  ```bash
  git push -u origin feature/us3-verify-meta-signature
  ```

### Mini-PR

- [ ] Open pull request inside the fork:
  - **base:** `integration`
  - **compare:** `feature/us3-verify-meta-signature`
  - **title:** `US-3: verify_meta_signature`
  - **body:** document the 3 manual verification cases and their results
- [ ] PR description confirms: no `on_message` changes, no secret hardcoded, 3 cases verified manually

---

## Edge cases to be aware of (don't fix now — already handled by the spec)

| Scenario | Handled by |
|---|---|
| Header present but value is `"sha256="` (empty after prefix) | `compare_digest("expected", "")` → always False |
| Header present but value has no `"sha256="` prefix (e.g., raw hex) | `startswith("sha256=")` guard → False before computation |
| Empty secret (`WHATSAPP_APP_SECRET` not set) | `not secret` guard → False before computation |
| Body is empty bytes (`b""`) | Valid — HMAC of empty bytes is still a deterministic hash |
| Unicode characters in secret | `secret.encode()` always UTF-8 — consistent with how Meta generates the token |

---

## Dependency map: where this function is consumed

```
US-3  verify_meta_signature()
         │
         └── US-9  on_message() — detects Shape B {"raw_body": bytes, "headers": dict}
                      │           calls verify_meta_signature; returns None if False
                      │
                      └── Test 7 (test_channel_specific_behaviour_signature_verification)
                              unsigned  → None  ✓
                              tampered  → None  ✓
                              valid     → ChannelMessage ✓
```

US-9 cannot be started until US-3, US-4, US-6, and US-7 are all merged to `integration`.
US-3 itself has zero predecessors.

---

## Quick reference: Mock constants used in tests

From `tests/channels/mocks/whatsapp_mock.py`:

| Constant | Value |
|---|---|
| `DEFAULT_APP_SECRET` | `"test-app-secret"` |
| `OWNER_WA_ID` | `"919999990000"` |
| `STRANGER_WA_ID` | `"917777770000"` |
| `PHONE_NUMBER_ID` | `"10987654321"` |

The test fixture `_set_secret` (autouse) does:
```python
monkeypatch.setenv("WHATSAPP_APP_SECRET", DEFAULT_APP_SECRET)
```
So during pytest runs, `WHATSAPP_APP_SECRET` is always `"test-app-secret"`.
