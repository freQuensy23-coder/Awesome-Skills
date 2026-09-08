---
name: music-editor
description: Use when editing lyrics in existing recorded music.
version: 1.0.0
author: Alexey Mametyev
license: MIT
metadata:
  hermes:
    tags: [music, audio, lyrics, inpainting, treblo, browser]
---

# Music Editor skill

## When to Use

Use this skill to replace sung words or a short lyric passage while retaining an existing recording's singer, melody, accompaniment, and approved earlier edits. It covers the entire job from a user's source audio and an authorized account to a verified, delivered MP3.

The preferred method is **Treblo v2.2 source-conditioned music inpainting**, followed by exact-window local composition. This method produced user-approved word edits and a later comic couplet. Text-to-speech, pitch-shaped speech, and generic song regeneration did not meet the same quality requirement. A successful model request is not proof of correct words or acceptable audio.

## Inputs and boundaries

Obtain the actual audio attachment/file, the exact requested replacement text, the scope of all repeated forms, and the delivery destination. Record which earlier version the user has approved. If a quoted value is unclear, do not silently normalize it. Resolve ordinary decisions from the request and recording; a genuinely missing permission, fresh authentication factor, or spending authorization remains a gate.

Use only recordings the user owns or has permission to edit/upload, and comply with any voice-consent requirements. Do not make a rights attestation on the user's behalf without that authorization. Keep account credentials, source recordings, generated audio, task receipts, and browser profiles in private working storage. The public skill deliberately contains none of those artifacts.

## Procedure

### 1. Prepare a recoverable local project

Install Python 3.11+, FFmpeg/ffprobe, and this folder's `requirements.txt` in a virtual environment. No local GPU is needed for hosted Treblo inference. An audio-capable LLM is optional for QA and may have separate costs.

Decode the supplied recording once to a FLOAT WAV master at its native rate/channel count. Keep that master immutable and hash every input. Make a task manifest with the literal request, source hash, target inventory, interval coordinates, candidate statuses, budget, approved baseline, QA evidence, and delivery receipt. Use the schema in [handoff and delivery](references/handoff-and-delivery.md). Save progress after each generation so a restarted agent does not submit duplicate jobs.

### 2. Inventory lyrics and plan a small musical edit

Listen to the actual recording with direct-audio transcription. Familiar-song recognition often reconstructs the old lyric incorrectly; request what is actually audible. Include all inflections/diminutives and repeated outro lines in the inventory. In the worked task, the scope was eleven regular forms and eight diminutives; a related standalone place name was outside scope. Those counts are an example, not a template for other songs.

For humor, locate a clear setup and a short unexpected payoff. Preserve the surrounding story, rhyme, syllable count, and stressed beats. Change the smallest coherent passage. A two-line couplet can sound more natural than forcing a long joke into a single word. [Musical editing and QA](references/editing-and-qa.md) explains boundary selection, word-only edits, donor reconstruction, and acceptance checks.

### 3. Register and establish the real entitlement

Read [accounts and limits](references/accounts-and-limits.md). Use the normal Treblo signup/Google OAuth flow with an account the user authorizes. Verify the signed-in account and the developer balance; do not assume an empty Plan screen means the signup promotion was applied. In a verified signup, creating the first named API key activated 1,500 free credits without a card.

The API and website have different observed entitlements. The same account completed a native website inpaint after its API balance reached zero. This is a legitimate alternate product path, not evidence of unlimited use. If an account is limited, follow the documented options in that reference. No free-account rotation strategy was tested; do not invent one or create accounts to evade a restriction. Paid top-ups require the user's budget authorization.

### 4. Choose the normal website or documented API

For a few edits, follow [browser control](references/browser-control.md): create/open a private project, upload the source with the required permission, select the source track, enter Replace mode, choose the interval and custom lyrics, verify v2.2, then submit once. Record the returned job/track identifiers and poll the exact project read-back. Complete the site's normal verification; stop at an unresolved human-only gate.

For repeatable word-sized batches with available API credit, follow [API operation](references/api.md). The exercised API differs from some documentation: it rejected `prompt` for inpainting but required a valid tag when lyrics were supplied. Use one mask per request and the masked passage's lyrics. Do not invent a v3 inpaint endpoint or confuse API Bearer keys with browser session credentials.

Download actual successful outputs promptly, preserving task IDs and hashes. If a request times out, recover its status before generating again. Content moderation, duplicate-upload rejection, and rate limits are separate problems; do not treat them as reasons to change identities or bypass the service.

### 5. Compose into the approved master

Provider output can modify the whole returned waveform, including ostensibly unedited audio. Measure alignment against several unedited musical windows and insert only the authorized local interval into a copy of the approved PCM master. Keep crossfades inside that interval. Preserve every previous accepted edit in a protected-interval manifest.

Use the portable commands in [script usage](references/scripts.md), implemented in [audio_edit.py](scripts/audio_edit.py). Their defaults fail closed on invalid bounds, overlap, clipping, and unsafe overwrites. A low waveform correlation can be caused by provider re-encoding; investigate source identity, lag consistency, and audible changes instead of weakening a threshold just to get a pass. If a larger context crop is used, keep its global time origin explicit; local and full-song timestamps are not interchangeable.

### 6. Verify the resulting MP3

Separate lexical correctness from acoustics. Count actual replacements across full chorus contexts and the entire song, including tails. Check the new couplet without supplying its intended wording to the transcriber. Compare singer, rhythm, music continuity, and seam audibility separately. Bind every QA result to its exact input hash and keep contradictory reports; do not keep rerunning until an auditor agrees.

The optional [audio_qa.py](scripts/audio_qa.py) sends only the selected audio to the explicitly configured audio-capable Gemini model using an environment key. Human listening can replace paid LLM QA. A separate blind A/B comparison should include an identical-audio control; a model saying two files are identical is not a byte comparison. Human approval is evidence of perception and should not be overruled by a previously pessimistic automated score.

Prove sample count/rate/channels, finite values, no clipping, equality outside the edit mask and inside protected intervals in the lossless master. Encode a real MP3, decode/probe it, and audit that delivered encoding. Lossy MP3 samples are not bit-identical to the original PCM. Do not re-encode a checked file after QA without updating the evidence.

### 7. Deliver and verify

Send the actual MP3 to the requested chat/topic or destination, not a plan or a local pathname alone. Read back the exact uploaded item; when available, download it and compare its SHA-256. For Telegram, preserve the current topic explicitly and distinguish Bot API from user-account message IDs. See [handoff and delivery](references/handoff-and-delivery.md). Completion requires delivered media with the intended contents. Preserve original audio, accepted files, reproducible scripts, and delivery evidence.

## Pitfalls

A word can be intelligible yet wrong; a regular form can be missed when only diminutives are enumerated. Subsecond masks can omit consonants, while longer masks can change neighboring lyrics. Browser `fill_input` may not update React state. Timeline dragging pans unless Select mode is active. Queued status can be stale until a fresh project read. API-zero does not prove website-zero. A provider's complete audio download is not a safe replacement for the entire approved master. Free compute does not guarantee a model's suitability.

Do not delete a current deliverable merely because an automated auditor dislikes it. Retain the evidence, explain uncertainty, and respect the user's explicit acceptance or request to hear a disclosed intermediate. Never mislabel an inferior or unverified version as finished.

## Verification

The job is complete when the exact replacement scope is covered, musical quality has been evaluated, unchanged/protected PCM regions are proved, a playable MP3 exists, and destination read-back confirms delivery. [Worked case and alternatives](references/worked-case.md) gives the observed successes and failures, including why the hosted method was preferred over free Colab experiments.

## Reference index

[Accounts and limits](references/accounts-and-limits.md) · [Browser control](references/browser-control.md) · [API](references/api.md) · [Editing and QA](references/editing-and-qa.md) · [Portable scripts](references/scripts.md) · [Worked case](references/worked-case.md) · [Handoff and delivery](references/handoff-and-delivery.md)

Dependencies: [requirements.txt](requirements.txt). The local tests in [tests](tests/) use synthetic audio and do not consume credits. See the repository README for the test command. All account entitlements, models, tags, and UI labels must be rechecked against the live service; observations here are dated September 2026.
