# Treblo public API: source-conditioned inpainting

Official documentation checked **2026-09-08**. Runtime observations labeled **2026-09-07** come from previously verified tests supplied for this guide, not a new inference run. The examples are reusable templates, not transcripts of those private requests. No paid inference was called for this documentation review.

## Choose the endpoint, not just the newest model

Base URL: **`https://api.treblo.com/v1`**. Here `v1` is the API specification version, while `v2` and `v3` in generation routes are model versions.

| Route | Purpose | Status in public docs checked 2026-09-08 |
| --- | --- | --- |
| `POST /generations/v2/inpaint` | Replace one interval inside source audio | Documented; v2 is deprecated |
| `POST /generations/v3` | Generate a new song | Documented as v3-preview/beta |
| `POST /generations/v3/extend` | Continue an existing song | Documented; not an inpainting substitute |
| `GET /generations/TASK_ID` | Read task state, parameters, and final audio paths | Preferred polling route here |
| `GET /generations/status/TASK_ID` | Read status only | JSON string by default; object with `include_alignment=true` |
| `GET /credits/balance` | Read API credit balances | Read-only preflight |

No v3 inpainting route was documented in the reviewed source. Do not invent `/v3/inpaint`, change model versions in the URL blindly, or replace a requested local edit with whole-song generation. The docs recommend v3 for new integrations, but that does not establish feature parity. Website model labels such as v2.2 do not by themselves establish public API routes. Recheck availability before each new integration because [API Terms §10](https://treblo.com/api-terms) permits deprecation and discontinuation.

## Prerequisites and read-only balance check

- Create one legitimate account and a named API key using [accounts-and-limits.md](accounts-and-limits.md).
- Use Python 3 and install the HTTP dependency with `python -m pip install requests` in your own environment.
- Inject `TREBLO_API_KEY` from your secret manager into the process environment. Never paste a bearer token into source, a command-line argument, a prompt, or a URL. Do not export browser cookies to authenticate API requests.
- Establish rights to the audio and lyrics and any required consent for identifiable voices. Sending `audio_base64` uploads the audio to Treblo; base64 is not encryption.

This example only reads the balance; it does not generate audio:

```python
import os
import requests

key = os.getenv("TREBLO_API_KEY")
if not key:
    raise SystemExit("Set TREBLO_API_KEY through your secret manager.")

response = requests.get(
    "https://api.treblo.com/v1/credits/balance",
    headers={"Authorization": f"Bearer {key}"},
    timeout=(10, 30),
    allow_redirects=False,
)
if response.status_code != 200:
    raise SystemExit(f"Balance check failed: HTTP {response.status_code}")
balance = response.json()
print({name: balance[name] for name in ("num_credits", "num_credits_payg")})
```

The documented fields are subscription and pay-as-you-go credits, respectively. The public pricing page currently lists **100 credits for one song** and **150 for two v2 songs**; these also match historical observations. Recheck pricing and the actual balance before approving a generation. An API balance does not establish website entitlements.

## Inpainting request contract and observed discrepancies

The following observations apply to `POST /v1/generations/v2/inpaint`, not every Treblo endpoint:

| Field or behavior | Operational rule | Evidence |
| --- | --- | --- |
| `prompt` | Omit it entirely for the historically working v2 inpainting request | **2026-09-07 runtime:** supplying it caused HTTP 422, despite its presence in the public schema still checked 2026-09-08 |
| `lyrics` and `tags` | Supply the replacement lyrics together with a nonempty supported style-tag list | **2026-09-07 runtime:** lyrics alone were insufficient; tags were required |
| `tags` values | Use exact vocabulary entries, not improvised descriptions | **2026-09-07 runtime:** `russian chanson` accepted; `male vocals` rejected. The current public Tag Explorer lists `russian chanson` and `male vocalist`; the latter is not asserted as a tested replacement |
| `audio_base64` | Send encoded context audio; alternatively use the documented `audio_url` method, not both | Base64 input tested historically; both methods documented |
| `sections` | Exactly one `[start_seconds, end_seconds]` pair inside an outer array; measured relative to the supplied audio | Documented and historically tested |
| Interval length | A **0.86-second** interval was accepted | Historical observation only; not a guaranteed minimum or evidence of acceptable word-edit quality |
| `selection_crop` | `false` retains surrounding output; `true` requests only the edited interval | Documented; `false` tested historically |

**Historically tested settings:** `num_songs=1`, `instrumental=false`, `output_format="wav"`, `selection_crop=false`, `align_lyrics=false`, `balance_strength=0.7`, with context in `audio_base64` and exactly one interval in `sections`.

The docs' general recommendation to start with only a prompt conflicts with the observed inpainting validation. Do not “repair” the working inpaint request by adding `prompt`, including an empty one, just to match generic generation guidance. If validation changes, inspect the actual field-level error privately, compare current endpoint-specific docs, and report the discrepancy rather than retrying paid variations blindly.

### Prepare the context and selection

1. Preserve the original audio. Prepare a context file containing the authorized edit plus useful surrounding music. Set boundaries by listening and measured timestamps; do not use guessed lyric offsets.
2. If the context was cropped from a longer track, translate the edit timestamps into **context-local seconds**. Validate `0 <= start < end <= context_duration` before submission. The example below checks ordering, but you must verify the decoded duration separately.
3. Supply one interval per request. A multi-word edit can use one contiguous interval if the user permits everything inside it to be regenerated. Disjoint edits cannot be sent as multiple `sections` in one request under the reviewed contract.
4. The docs state a **40 MB file-size limit for base64 audio**, without clarifying the exact size-accounting boundary. Check both source and encoded request size conservatively; do not assume a 40 MB source file plus base64 overhead is accepted.
5. For an existing Treblo generation, the docs recommend its original CDN audio URL so Treblo can reuse latent representations and avoid repeated re-encoding. Use only an authorized source URL that is still available. For local audio, `audio_base64` avoids making your source publicly accessible, but still transmits it to the provider.

### Build and explicitly approve one submission

Save this template as a local script. Set `TREBLO_CONTEXT_AUDIO` to your authorized context file, `TREBLO_EDIT_START_SECONDS` and `TREBLO_EDIT_END_SECONDS` to measured boundaries, and `TREBLO_REPLACEMENT_LYRICS` to the approved text. Choose appropriate tags from the [Tag Explorer](https://treblo.com/tag-explorer); the default below demonstrates a historically accepted style, not a recommendation for every song.

Running the script prepares the payload but **does not send it** unless you type `SUBMIT ONE BILLABLE EDIT` after checking the current balance and price. Even a trial-credit request consumes quota. This is a single POST with no automatic retries.

```python
import base64
import math
import os
from pathlib import Path
import requests


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing environment variable: {name}")
    return value


def build_payload():
    start = float(required_env("TREBLO_EDIT_START_SECONDS"))
    end = float(required_env("TREBLO_EDIT_END_SECONDS"))
    if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end):
        raise ValueError("Use finite, ordered context-local timestamps.")
    audio = Path(required_env("TREBLO_CONTEXT_AUDIO")).read_bytes()
    if not audio:
        raise ValueError("Context audio is empty.")
    encoded = base64.b64encode(audio).decode("ascii")
    # Conservative local guard, not a verified server size formula.
    if len(encoded) >= 39_000_000:
        raise ValueError("Reduce context size and recheck provider limits.")
    lyrics = required_env("TREBLO_REPLACEMENT_LYRICS")
    if not lyrics.strip():
        raise ValueError("Replacement lyrics must not be whitespace only.")
    return {
        "audio_base64": encoded,
        "tags": [os.getenv("TREBLO_STYLE_TAG", "russian chanson")],
        "lyrics": lyrics,
        "sections": [[start, end]],
        "num_songs": 1,
        "instrumental": False,
        "output_format": "wav",
        "selection_crop": False,
        "align_lyrics": False,
        "balance_strength": 0.7,
    }


def main():
    key = required_env("TREBLO_API_KEY")
    payload = build_payload()
    print("Confirm rights, decoded duration, boundaries, balance, and price first.")
    if input("Type SUBMIT ONE BILLABLE EDIT to send: ") != "SUBMIT ONE BILLABLE EDIT":
        print("Not submitted.")
        return
    try:
        response = requests.post(
            "https://api.treblo.com/v1/generations/v2/inpaint",
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
            timeout=(10, 120),
            allow_redirects=False,
        )
    except requests.RequestException:
        raise SystemExit(
            "Transport error: acceptance is unknown. Reconcile the account; "
            "do not automatically resubmit."
        ) from None
    if not 200 <= response.status_code < 300:
        raise SystemExit(
            f"HTTP {response.status_code}: inspect the error privately; do not auto-retry."
        )
    result = response.json()
    task_id = result.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise SystemExit("Missing task_id: reconcile the account before any resubmission.")
    print("Accepted. Poll this task; do not submit it again.")
    print("Task ID (keep private):", task_id)
    # Never publish this identifier or the associated private request record.
    return task_id


if __name__ == "__main__":
    TASK_ID = main()
```

HTTP success and a task ID mean accepted/queued, not a finished or musically acceptable edit. Preserve the returned task ID in your private job record. If a network timeout or malformed response leaves acceptance uncertain, do not create another job merely because the first response was lost.

## Poll the existing task; do not resubmit

Use the full task endpoint to obtain both `status` and `song_paths`. In this template, **`TASK_ID` is symbolic**: replace it locally with the exact ID returned by your request. The timeout and five-second interval below are client choices, not a documented rate allowance or completion guarantee.

```python
import os
import time
from urllib.parse import quote
import requests


def wait_for_task(task_id, max_wait_seconds=900):
    key = os.getenv("TREBLO_API_KEY")
    if not key:
        raise ValueError("Missing TREBLO_API_KEY")
    url = "https://api.treblo.com/v1/generations/" + quote(task_id, safe="")
    deadline = time.monotonic() + max_wait_seconds
    while time.monotonic() < deadline:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {key}"},
            timeout=(10, 30),
            allow_redirects=False,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Polling stopped: HTTP {response.status_code}")
        result = response.json()
        if not isinstance(result, dict):
            raise RuntimeError("Unexpected full-task response type")
        status = result.get("status")
        if status == "FAILURE":
            raise RuntimeError("Generation failed; inspect error_message privately.")
        if status == "SUCCESS":
            paths = result.get("song_paths")
            if not isinstance(paths, list) or not paths or not all(
                isinstance(path, str) and path.startswith("https://") for path in paths
            ):
                raise RuntimeError("SUCCESS without usable song_paths; reconcile task.")
            return result
        time.sleep(5)
    raise TimeoutError("Local wait expired. Resume polling the same task, not a new POST.")


# Replace the symbolic value locally. Do not publish returned audio URLs.
TASK_ID = "TASK_ID"
# result = wait_for_task(TASK_ID)
# song_urls = result["song_paths"]
```

For the lightweight route **`GET /v1/generations/status/TASK_ID`**, `response.json()` may be a string such as `"GENERATING"` or `"SUCCESS"`, not a dictionary. Normalize it with `status = data if isinstance(data, str) else data["status"]`. The current docs explicitly describe that string response; adding `include_alignment=true` requests an object containing `status` and `alignment_status`. Do not invent a trailing `/TASK_ID/status` route. After status-only success, fetch the full task to obtain `song_paths`.

## Download, validate, and handle failures

- Download every returned candidate you intend to keep. The docs state that songs are deleted after **one week (168 hours)**; later availability is not guaranteed. Returned audio URLs are **unlisted, not access-controlled**. Anyone with a URL can fetch it. Keep URLs, task records, and audio private.
- Fetch audio URLs without forwarding your API bearer header to the CDN or another host. Do not log URLs or full task responses into public artifacts; task data can contain source references, prompts, and lyrics.
- Decode the downloaded file fully and verify expected duration and format. Listen to the edited words, vocal continuity, accompaniment, and both boundaries. A 0.86-second accepted request does not establish accurate singing or clean transitions.
- `selection_crop=false` does not promise that decoded samples outside the selection are identical. If the requirement is “change only these words,” validate outside-region samples or splice an accepted replacement into the original under the user's permitted boundaries. Do not claim sample identity after whole-track lossy re-encoding.
- For **422**, distinguish schema errors (such as the historical rejected `prompt` or invalid tag) from content moderation or duplicate-upload rejection. Correcting a schema is legitimate; obfuscating lyrics/audio or rotating accounts to defeat filtering is not. See [accounts-and-limits.md](accounts-and-limits.md).
- For authentication, quota, or rate-limit errors, stop and diagnose the exact response. Respect any provider retry guidance for reads. Never automatically retry a generation POST with uncertain acceptance, and never create keys/accounts to circumvent limits.
- The docs say a main generation `FAILURE` deducts no credits; they also say alignment failure after successful generation still incurs credits. Treat this as documented billing behavior, not a verified refund for every HTTP error. Read the balance and reconcile the specific job when billing is unclear.

## Official sources and policy scope

Checked **2026-09-08**:

- [API documentation](https://treblo.com/developers/docs): inpaint schema, one-section restriction, size limit, deprecation, status response shapes, balance fields, and retention.
- [Tag Explorer](https://treblo.com/tag-explorer): current supported tag vocabulary.
- [API pricing](https://treblo.com/developers/pricing): current advertised per-job costs, not future guarantees.
- [API Terms](https://treblo.com/api-terms), dated **2026-08-20**: authorized API automation (§2); qualified output ownership (§3); no API-input/output model training and no publication to public service areas (§4); prominent Treblo attribution for user-facing API implementations (§6); confidential, non-transferable keys (§7); credits (§8); anti-circumvention, input rights, and identifiable-voice consent (§9); availability (§10).
- [Terms of Service](https://treblo.com/tos), dated **2026-08-20**: incorporated service terms. API-specific exceptions do not grant permission to automate the website's internal endpoints.

The API's privacy provisions do not establish identical handling for website uploads, and unlisted output URLs still need protection. None of these terms guarantees copyrightability, uniqueness, exact voice preservation, or successful editing of every submitted recording.
