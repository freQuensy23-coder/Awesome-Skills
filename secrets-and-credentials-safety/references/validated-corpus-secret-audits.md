# Validated secret audits for training corpora

Use this workflow when auditing conversations, datasets, archives, or model-training exports for credentials.

## Non-mutating boundary

- Treat audit, redaction, rotation, and deletion as separate operations.
- A request to find/report secrets authorizes read-only analysis only.
- Capture source size, record count, and preferably a checksum before the audit; verify them again afterward.
- Never overwrite the source. Write masked reports to a separate directory.
- If the user cancels cleanup, stop redactors immediately and preserve every source and derived artifact unless explicitly told otherwise.

## Two-stage audit

1. Detection: use exact provider signatures plus broad candidate rules. Keep coordinates such as conversation/share ID, message ID, role, and field.
2. Validation: assign a verdict to every unique candidate and every occurrence. Unresolved candidates must remain visible in the report.

Regex output is preliminary evidence. Validate with:

- USER vs ASSISTANT role and whether the assistant copied a USER value;
- masked surrounding context and assignment syntax;
- exact provider length/alphabet/prefix;
- JWT header/payload decoding, algorithm, claim keys, and expiry;
- PEM parsing with OpenSSL or a crypto library;
- URL parsing, userinfo detection, query/fragment parameter names, host, and signed-URL expiry;
- entropy and character profile;
- placeholder/type/reference recognition;
- manual review of ambiguous USER-origin candidates.

Common false positives include `request.POST['password']`, `import.meta.env.CLIENT_SECRET`, `this.options.clientSecret`, `res.data.access_token`, language type names, generated defaults, malformed templates, and numeric resource IDs that resemble tokens.

## Safe validation boundary

Do not test leaked third-party credentials against provider APIs. Active checks could use or alter someone else's account. Offline structural, cryptographic, expiry, provenance, and contextual validation is sufficient to decide whether material must be excluded from training.

Distinguish:

- confirmed credential material;
- sensitive client/project identifiers (for example Firebase client API identifiers);
- expired signed-URL credentials;
- generated/copied credential-shaped material that should still be scrubbed from training;
- placeholders/examples;
- proven structural collisions and code references.

## Reporting

Reports must not contain raw third-party secrets. Store:

- type and verdict;
- masked preview;
- value length and SHA-256 fingerprint;
- conversation/share ID, message ID, role, and field;
- safe structural metadata such as host, JWT claim names, or expiry;
- sanitized context;
- explicit flags stating whether external APIs were contacted and whether the source changed.

Report confirmed and potential values separately. Deduplicate by secret fingerprint so USER values copied by ASSISTANT are not double-counted.

## Future redaction

Build and test redaction on an isolated copy only after explicit authorization. Redact every duplicate representation, including normalized fields, raw message copies, rendered URLs, and nested metadata. Re-scan the sanitized output and require zero non-placeholder findings before using it for training.
