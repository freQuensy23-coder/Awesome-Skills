# Separate delivery of Алексей's own secrets in a private Telegram chat

Use when Алексей asks for credentials in a separate Telegram message while the current response must contain a non-secret artifact or repository link.

## Workflow

1. Inventory credentials from the final tracked runtime code after pruning dead stages. Include only auth paths the current product executes; keep unrelated high-impact account tokens and credentials used only by failed experiments or agent-side delivery out of the bundle unless explicitly requested. Examples: a Vertex ADC pipeline does not need an unrelated Gemini API key; removing a `gog`/Drive uploader removes its OAuth credential; deleting proxy/backfill experiments removes proxy and Facebook-session credentials.
2. Read each value from its authoritative credential store; do not transcribe from memory.
3. Build the message in a temporary file with mode `0600`. Keep it below Telegram's single-message limit when practical.
4. Send through Hermes' configured gateway without exposing the bot token:
   `hermes send --to telegram:<chat_id> --file <temporary-file> --json`
5. Require `success: true` and record the returned `message_id` before claiming delivery.
6. Delete temporary exported OAuth-token files and temporary plaintext bundles after verified delivery.
7. Keep repository/source delivery separate. Run a current-tree secret scan before push, verify the repository is private, and never commit the credential bundle.

The message must contain Алексей's requested values fully and exactly. Do not mask or shorten them in his private chat.