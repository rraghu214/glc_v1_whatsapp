# B1: schemas.py typed wrappers — Strategy & Checklist

**Branch:** `feature/usb1-schemas`
**Files changed:** `glc/channels/catalogue/whatsapp/schemas.py`, `glc/channels/catalogue/whatsapp/adapter.py`, `glc/channels/catalogue/whatsapp/tests/test_twilio_path.py`
**Depends on:** US-3, US-4, US-5, US-6, US-7, US-8 (all parse/build helpers must exist first)
**Feeds into:** nothing (backlog item — pure style, zero grading impact)

---

## Strategy

### What B1 delivers

Pydantic models in `schemas.py` that replace the raw `dict[str, Any]` return types used by the four parse/build helpers. The functions now return typed model instances; callers use attribute access instead of dict-key access. At every boundary where a plain dict is required (HTTP calls, mock send log assertions), `.model_dump()` is called.

### Models

| Model | Wraps | Fields |
|---|---|---|
| `MetaParsed` | `parse_meta_payload` return | `from_id`, `text`, `message_id`, `timestamp: str`, `profile_name` |
| `TwilioParsed` | `parse_twilio_payload` return | `from_id`, `text`, `message_id`, `timestamp: datetime`, `profile_name` |
| `MetaSendText` | nested inside `MetaSendPayload` | `body` |
| `MetaSendPayload` | `build_meta_send_payload` return | `messaging_product`, `to`, `type`, `text: MetaSendText` |
| `TwilioSendPayload` | `build_twilio_send_payload` return | `To`, `From`, `Body` |

### Key design decisions

**One model per parse function, not a shared base.** `MetaParsed.timestamp` is `str` (Unix epoch string from Meta's JSON); `TwilioParsed.timestamp` is `datetime` (server receipt time, no timestamp in Twilio's wire format — see HANDOFF §0.1). A shared base would require `str | datetime` which forces the caller to narrow the type anyway.

**`isinstance` narrowing in `_to_channel_message`.** The function accepts `MetaParsed | TwilioParsed`. The timestamp branch already keyed off `provider == "meta"` — replaced with `isinstance(parsed, MetaParsed)` so mypy can narrow the type and confirm `parsed.timestamp` is `str` in the Meta branch and `datetime` in the Twilio branch. No `# type: ignore` needed.

**`.model_dump()` only at boundaries.** The HTTP helpers (`_send_meta`, `_send_twilio`) call `.model_dump()` internally before `httpx.post(json=...)` / `httpx.post(data=...)`. The `send()` method calls `.model_dump()` before every `mock.send(...)` call. This ensures the mock's `send_log` always contains plain dicts, which is what the fixed test assertions check.

**`TwilioSendPayload.From` is valid Python.** `From` (capital F) is not a Python keyword — only `from` (lowercase) is. Pydantic v2 accepts it as a field name and `model_dump()` preserves the capitalisation, matching Twilio's expected form-body keys exactly.

**`MetaSendPayload.model_dump()` produces the exact Meta wire shape.**
```python
MetaSendPayload(to="123", text=MetaSendText(body="hi")).model_dump()
# → {"messaging_product": "whatsapp", "to": "123", "type": "text", "text": {"body": "hi"}}
```
Pydantic v2 recursively serialises nested models in `model_dump()` — no custom override needed.

### What B1 does NOT do

- Does NOT change the external interface of `Adapter.on_message` or `Adapter.send`
- Does NOT touch any file outside the owned path
- Does NOT affect grading — the course's own stub leaves `schemas.py` commented out, and the fixed tests only call `on_message`/`send`, never the parse/build helpers directly

---

## Checklist

### Pre-flight

- [x] Confirm active branch is `feature/usb1-schemas`, branched from `integration`
- [x] All US-3 through US-8 helpers already exist in `adapter.py`

### Implementation — schemas.py

- [x] Uncommented and filled `schemas.py` with 5 Pydantic v2 `BaseModel` subclasses
- [x] `MetaParsed`: `from_id: str`, `text: str | None`, `message_id: str`, `timestamp: str`, `profile_name: str | None`
- [x] `TwilioParsed`: same fields except `message_id: str | None` and `timestamp: datetime`
- [x] `MetaSendText`: `body: str` (nested inside `MetaSendPayload`)
- [x] `MetaSendPayload`: `messaging_product: str = "whatsapp"`, `to: str`, `type: str = "text"`, `text: MetaSendText`
- [x] `TwilioSendPayload`: `To: str`, `From: str`, `Body: str`

### Implementation — adapter.py

- [x] Added import block for all 5 schema types
- [x] `parse_meta_payload` return type changed from `dict[str, Any] | None` → `MetaParsed | None`; constructs `MetaParsed(...)` instead of returning a raw dict
- [x] `parse_twilio_payload` return type changed from `dict[str, Any] | None` → `TwilioParsed | None`; constructs `TwilioParsed(...)` instead of returning a raw dict
- [x] `build_meta_send_payload` return type changed from `dict[str, Any]` → `MetaSendPayload`; constructs `MetaSendPayload(to=..., text=MetaSendText(body=...))`
- [x] `build_twilio_send_payload` return type changed from `dict[str, str]` → `TwilioSendPayload`; constructs `TwilioSendPayload(To=..., From=..., Body=...)`
- [x] `_to_channel_message` signature updated to `MetaParsed | TwilioParsed`; all dict-key access replaced with attribute access; timestamp branch uses `isinstance(parsed, MetaParsed)` for mypy narrowing
- [x] `on_message`: `parsed` type annotation updated to `MetaParsed | TwilioParsed | None`; `parsed["from_id"]` → `parsed.from_id` throughout
- [x] `_send_meta` signature updated to `MetaSendPayload`; calls `payload.model_dump()` before `httpx.post(json=...)`
- [x] `_send_twilio` signature updated to `TwilioSendPayload`; calls `payload.model_dump()` before `httpx.post(data=...)`
- [x] `send()`: all 4 `mock.send(payload)` calls updated to `mock.send(payload.model_dump())`

### Implementation — test_twilio_path.py

- [x] Added import of `MetaSendPayload`, `MetaSendText`, `TwilioSendPayload` from `schemas`
- [x] `test_send_meta_returns_structured_error_for_non_json_response`: direct `_send_meta` call updated to pass `MetaSendPayload(to=OWNER_ID, text=MetaSendText(body="test"))`
- [x] `test_send_twilio_returns_structured_error_for_non_json_response`: direct `_send_twilio` call updated to pass `TwilioSendPayload(To=..., From=..., Body=...)`
- [x] `test_send_falls_back_to_twilio_on_meta_131030_and_caches_provider`: monkeypatched fakes updated — `fake_send_meta` uses `payload.to` (attribute access); `fake_send_twilio` uses `payload.model_dump() == {...}`

### Quality gates

- [x] `pytest tests/channels/test_whatsapp.py` → **7/7 passed**
- [x] `pytest glc/channels/catalogue/whatsapp/tests/test_twilio_path.py` → **15/15 passed**
- [x] `ruff check glc/channels/catalogue/whatsapp/` → **clean** (2 issues auto-fixed: unused import + unsorted import block in test file)
- [x] `mypy glc/channels/catalogue/whatsapp/` → **Success: no issues found in 8 source files**
- [x] `check_pr_boundaries.py --base integration --head HEAD` → **OK: 0 files changed outside owned paths**
- [x] `scorecard.py --base integration --head HEAD` → **10.0/10**

### Scorecard note — group marker format

The scorecard regex is `[\w-]+` (no spaces). Use `# Group: group-whatsapp` in the final PR body, not `# Group: Group WhatsApp`. The HANDOFF §10 note about matching `GROUPS.md` exactly applies to the boundary check normaliser, not the scorecard regex.

### Commit

- [x] Staged: `glc/channels/catalogue/whatsapp/schemas.py`, `adapter.py`, `tests/test_twilio_path.py`, `help_docs/USB1_schemas/`
- [x] Committed: `B1: add Pydantic typed wrappers in schemas.py; flow through adapter`

### Mini-PR

- [ ] Open pull request inside the fork:
  - **base:** `integration`
  - **compare:** `feature/usb1-schemas`
  - **title:** `B1: schemas.py typed wrappers`
  - **body:** note that this is a backlog item (pure style, zero grading impact); all 22 tests pass; scorecard 10/10
- [ ] Mini-PR approved and merged to `integration`