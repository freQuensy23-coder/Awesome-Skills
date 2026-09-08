# Worked case and failed alternatives

## What actually worked

A real September 2026 task changed eleven occurrences of a regular sung word and eight of its diminutive, then added a comic couplet while preserving all nineteen earlier changes. The user approved the nineteen-word version and subsequently said the couplet version looked awesome. This is a description of a tested method, not a distribution of the source recording or a guarantee of identical future generation.

Treblo v2.2 supplied the replacement singing. Native source-context inpainting produced the initial word candidates. Some expanded regular-word edits reused clean native-singing prefixes, with MelBandRoformer separation and local FFmpeg/RubberBand duration, pitch, envelope and phase alignment. Free Google Colab NVIDIA Tesla T4 runtimes provided separation/experimentation; Treblo inference itself ran on the provider's infrastructure. The delivered audio contained no TTS or ACE-Step material.

The later couplet used the existing uploaded source in the free web editor on the same account while both API credit fields were zero. The generated custom lines were:

> Она подняла руки, поправляя платье,
> А я под мышками увидел всю тайгу.

The joke follows the existing romantic setup, with the physical reveal at the end of the second line. These are the newly authored replacement lines; the original song and full copyrighted lyrics are not included.

The native mask was approximately 122.879–129.599 seconds. The local splice was 122.72–129.78 seconds with 55 ms cosine fades inside it. These timestamps are specific to that recording. Two real website takes completed. Blind transcription matched both intended lines in the first; the second sang singular «руку». Both passed the acoustic checks, so the first was selected on lexical evidence.

Only the couplet was copied into the approved nineteen-word FLOAT master. The complete master duration and all earlier edit intervals remained unchanged. The final stereo MP3 was 196.44 seconds and 7,858,605 bytes, delivered as native Telegram audio and verified by a byte-identical download. No paid Treblo top-up or subscription was purchased.

During packaging, the portable splicer was also exercised locally against the retained real generation, after explicit rate conversion and construction of a registered donor canvas. It reproduced the accepted FLOAT master sample-for-sample. The test inputs stayed private. This replay validates composition; it does not promise that a fresh cloud generation or a different MP3 encoder setting reproduces the same bytes.

## What did not establish comparable quality

ACE-Step 1.5 was genuinely run on a free Colab T4. Four SFT repaint trials completed at 50 steps, but successful inference did not establish accurate replacement lyrics or acceptable sound. The user preferred the hosted Treblo version. Do not silently replace the preferred workflow with ACE-Step merely because its weights are open source.

Some T4 configurations produced NaNs with float16. FP32, CPU offload and tiled decoding made inference numerically viable, but that did not resolve quality. The pinned experiment used ACE-Step repository commit `ca1e85fe9430179831e6bc6be790c332190a3866`. This is historical reproducibility context, not a recommendation to install that revision instead of inspecting current upstream instructions.

YingMusic CPU phoneme-conditioned experiments and speech-donor/PSOLA/WORLD approaches were also investigated. Speech synthesis and obvious montage were rejected. The separator used from the YingMusic repository is distinct from that repository's singing generator. Do not confuse using a separator checkpoint with choosing its singing model for the final audio.

## How another agent starts fresh

Bring your own authorized recording, literal replacement request, account and delivery destination. Follow SKILL.md, register through the normal flow, verify entitlements, inventory all occurrences, generate a representative native edit, and validate it. Preserve successful outputs, assemble only authorized intervals, and deliver the actual checked MP3. You do not need the original operator's credentials, personal browser, audio files, private IDs or session history.

An identical new task can require different masks, candidates and resources. Exact waveform reproduction would require the same source, retained generated artifacts and postprocessing inputs; a fresh stochastic generation is not promised to be byte-identical. Free access and GPU availability must be checked at runtime.
