# Awesome Skills

Practical agent skills with reproducible procedures, tested utilities, and documented failure modes.

## Music Editor skill

[Open the skill](music-editor/SKILL.md).

Edit words or short lyric passages in an existing recording with Treblo music inpainting, preserve the approved performance outside the edit, check the resulting audio, and deliver a real MP3. The package covers account registration, free API credits versus free website access, exhausted-limit options, browser control, exact-window audio composition, and delivery verification.

The workflow was exercised with real Treblo v2.2 generations in September 2026. Fresh-account promotions, prices, models, and UI controls can change; dated observations are identified as such. The included local tests exercise audio processing on synthetic fixtures, not fabricated provider results. No recording, credential, browser session, or private account identifier is distributed.

### Use with Hermes

Review the files first, then install through Hermes' normal security-scanning path:

```bash
hermes skills install freQuensy23-coder/Awesome-Skills/music-editor
```

Invoke `/music-editor` in a new session. See the [official skills documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/) if your installed CLI has different options. Other agents can read `music-editor/SKILL.md` and its linked references directly.

### Reproduce the local checks

```bash
git clone https://github.com/freQuensy23-coder/Awesome-Skills.git
cd Awesome-Skills
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r music-editor/requirements.txt
python -m unittest discover -s music-editor/tests -v
```

FFmpeg and ffprobe must be installed and on PATH. Refer to [script usage](music-editor/references/scripts.md) for the exact processing and QA commands. Network inference is opt-in and requires your own authorized account and input rights.

## Scope and privacy

"Awesome Skills" is the display title; GitHub assigned the repository slug `Awesome-Skills`. The Music Editor skill is self-contained: it does not require its author's local skills, project directory, account, or past conversations. It reproduces the method, not a promise of byte-identical stochastic music generation.

When a free allowance ends, use the provider's documented alternatives. This repository does not supply disposable-account farming, payment avoidance, CAPTCHA bypass, or content-filter evasion.

## License

The original documentation and utilities in this repository are available under [MIT](LICENSE). Music inputs, third-party models, generated output rights, and service usage remain subject to their respective licenses and terms.
