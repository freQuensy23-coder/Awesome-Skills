# Recoverable handoff and verified delivery

## Private task manifest

Keep a private JSON manifest beside the working audio, outside the skill repository. Record the literal request; authorized scope and budget; source path/hash; PCM sample rate, channels and frame count; approved baseline path/hash; each original/replacement word; each global and context-local interval; context origins; requested and completed candidate counts; provider task/track IDs and terminal states; local downloaded files/hashes; protected intervals; composition settings; immutable QA input hashes/prompts/results; human acceptance; and final delivery state.

Use explicit state values such as prepared, submitted, generating, downloaded, checked, delivered and delivery_verified. Saving submitted task IDs before polling prevents duplicate generation after a reset. For multi-item edits, append each batch to JSON/CSV and deduplicate/count in code; do not claim an exhaustive total from memory. Persist exact errors and contradictory QA rather than replacing them with a success summary.

A new agent needs this manifest plus authorized private inputs, not exported cookies or a public dump of prior conversations. The repository supplies the procedure; account access and recordings remain private. A public source URL or private task ID can expose audio and must not be copied into public documentation or commits.

## Completion means media at the destination

Send the checked MP3 using the user's requested platform. A local pathname, a proposed script, a successful generation response or a promise to send is not delivery. Keep the source and final artifact until the remote item is verified. Do not delete an imperfect current render solely because an automated auditor is pessimistic.

For Hermes, use the current platform's supported media path. See the [official skill-output documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/#skill-output-and-media-delivery). If the platform did not attach media, use another authorized delivery path and verify it instead of repeating a bare pathname.

## Telegram example

Obtain the current destination and topic from the actual session, never from a published example or old task. Use the configured bot or authorized platform tool. Native MP3 `sendAudio` is playable; `sendDocument` with `disable_content_type_detection=true` forces a downloadable document. Set `chat_id` and, when applicable, `message_thread_id` explicitly. A private bot chat can use topics even when a broad chat lookup does not expose a conventional forum flag.

Before sending, verify the bot identity and final file hash. Avoid automatic POST retries after ambiguous transport failures; read the destination first. Save the returned message ID, actual chat/topic, media type, filename, byte count and file ID. Read back the exact destination to confirm the unique caption/media. If `getFile` is available, download the returned file and compare SHA-256 with the checked local MP3. Do not log Bot API token-bearing URLs.

Telegram may normalize punctuation in filenames. Compare bytes/hash rather than requiring exact punctuation equality. Bot API and user-account MTProto message IDs use different namespaces; do not pass a Bot API ID to an MTProto context lookup. If a mistakenly routed duplicate exists, verify the correct-topic delivery before considering removal of that just-created duplicate.

## Privacy before sharing a skill

Publish only authored procedures, portable utilities and synthetic tests. Exclude .env files, API keys, browser profiles, cookies, audio, screenshots, raw HAR/network captures, private project IDs, source CDN URLs, user chat IDs, receipts, local absolute paths and session logs. Inspect the entire intended public Git history as well as the current files. Keep the reusable skill independent of those private artifacts; never claim that deleting a secret only from HEAD removes it from old commits.
