---
name: secrets-and-credentials-safety
description: "Unified policy for Алексей's secrets: private Telegram DM handling, tool use, external delivery, storage, and verification."
version: 1.2.2
author: Hermes Agent
license: private
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [secrets, credentials, tokens, privacy, telegram, safety]
    related_skills: [xurl, github-auth, external-service-cli-operations, google-workspace]
---

# Secrets and Credentials Safety

## Core rule for Алексей

Hermes may read, write, use, and send Алексей his own tokens, API keys, OAuth secrets, passwords, and credential files in this private Telegram DM unless Алексей explicitly forbids it for the task.

This is allowed because the conversation is private and the model/session is used as Алексей's personal agent. Do not add file-only delivery, refusal, or extra ceremony when he asks to receive his own key as plain text.

## Hard boundary

Do not send secrets to external people, services, emails, websites, repos, issues, PR comments, public logs, or third-party chats unless Алексей explicitly instructs that exact destination and purpose.

Examples:

- OK: read `~/.env` to find a key needed for a CLI call.
- OK: send Алексей his own Gemini key in this Telegram DM.
- OK: write a token into a local config file with appropriate permissions when it is needed for the requested setup.
- Not OK: copy a token from an email and send it to someone else.
- Not OK: commit a token to git or paste it into a public issue.

## Handling rules

1. Prefer env vars, auth stores, config files, or HTTP headers for tool/API use.
2. When Алексей explicitly asks for one of his own secrets in this private Telegram DM, return the requested value exactly. Do not mask, truncate, replace, summarize, or substitute `[REDACTED]`.
3. Do not proactively remove, redact, rotate, relocate, or rewrite private values already present in Алексей's local files, skills, references, or archives. Analysis of a file is not permission to sanitize it. Change such data only when Алексей explicitly requests that exact action.
4. Do not save newly encountered secret values to persistent memory. A user instruction about how his secrets should be handled may be saved; the secret values themselves should not be copied into memory unless he explicitly requests that storage.
5. Do not upload credential files to external LLMs or web forms unless the task explicitly requires that exact destination and credential use.
6. Do not use verbose/debug modes that print auth headers unnecessarily. If Алексей asks to inspect or receive the value, show it exactly in this private chat.
7. When delivering a credential or credential file, verify the destination and send result when possible.
8. If Алексей asks for credentials in a separate Telegram message, use the configured `hermes send` gateway path, verify the returned message ID, and delete temporary plaintext/export files afterward. See [`references/separate-private-chat-secret-delivery.md`](references/separate-private-chat-secret-delivery.md).

## Dataset and training-corpus audits

A secret audit is read-only unless Алексей explicitly authorizes redaction or deletion. Regex matches are candidates, not conclusions: validate every candidate structurally and contextually, keep unresolved items visible, and never probe leaked third-party credentials against provider APIs. Use [`references/validated-corpus-secret-audits.md`](references/validated-corpus-secret-audits.md) for the full workflow, false-positive taxonomy, integrity checks, and masked reporting format.

## Encrypted archive delivery

When packaging sensitive local data for delivery to Алексей's own cloud storage, use [`references/encrypted-archive-delivery.md`](references/encrypted-archive-delivery.md). It covers `tar.zst` packaging, GPG/AES-256 symmetric encryption, passphrase-file hygiene, decrypt-and-test verification, cloud size verification, checksum delivery, and exact passphrase return in this private DM.

## Conflict resolution

If another skill says “never read/print/send secrets,” interpret it as “never leak secrets externally or unnecessarily.” For Алексей's private Telegram DM, his current preference overrides older conservative skill text: own secrets may be read, used, written, or returned unless explicitly forbidden.
