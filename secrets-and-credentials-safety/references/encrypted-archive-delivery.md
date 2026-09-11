# Encrypted archive delivery to the owner

Use this workflow when Алексей asks to package sensitive local data and deliver it to his own cloud storage.

## Packaging and encryption

1. Confirm the requested source scope and measure source size plus available disk space.
2. Create a `tar.zst` archive with `tar --zstd`; keep it outside the source tree so it cannot archive itself.
3. Generate a high-entropy random passphrase with a CSPRNG. Store it temporarily in a mode-`0600` file; never interpolate it into a command line or expose it through process arguments.
4. Encrypt the completed archive with GPG symmetric encryption using AES-256, loopback pinentry, the passphrase file, SHA-512 S2K digest, and a high S2K count. Disable GPG's internal compression because Zstandard already compressed the payload.
5. Verify by decrypting as a stream into `zstd -t`. A successful encryption command alone is insufficient.
6. Compute SHA-256 of the encrypted artifact. Remove the unencrypted intermediate only after verification succeeds.

## Upload and verification

- Upload only the encrypted artifact unless the user explicitly requests plaintext.
- Upload a small `.sha256` companion file when useful.
- Read back cloud metadata and compare the remote byte size with the local encrypted file.
- Return the exact object link/ID, size, SHA-256, encryption method, full passphrase, and concise decryption/extraction commands.
- In Алексей's private Telegram DM, provide his generated passphrase fully and without masking when he asked for it.
- Do not make the object publicly shared unless explicitly requested; uploading to his account is distinct from publishing a public link.

## Cleanup

After capturing the passphrase for the final response, securely remove the temporary passphrase file. Keep or remove the local encrypted artifact according to the user's retention request; do not silently delete source data.

## Example command shape

- Encrypt: `gpg --batch --yes --pinentry-mode loopback --passphrase-file "$PASSFILE" --symmetric --cipher-algo AES256 --s2k-mode 3 --s2k-digest-algo SHA512 --compress-algo none --output "$ARCHIVE.gpg" "$ARCHIVE"`
- Verify: `gpg --batch --quiet --pinentry-mode loopback --passphrase-file "$PASSFILE" --decrypt "$ARCHIVE.gpg" | zstd -t`
- Decrypt: `gpg -o data.tar.zst -d data.tar.zst.gpg`
- Extract: `tar --zstd -xf data.tar.zst`
