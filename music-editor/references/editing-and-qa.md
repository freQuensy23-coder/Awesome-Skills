# Musical editing and quality checks

## From source recording to a target inventory

Preserve the supplied file and hash it. Decode once to FLOAT PCM, preserving sample rate and channels. Listen/transcribe the recording directly and inventory every requested occurrence, including grammatical forms and repeated endings. Store each occurrence's text, replacement, global time window and approval state. Use original-vocal alignment when mixture alignment is unclear. Alignment is an estimate: consonant starts, held vowels, reverberation and backing vocals often extend beyond the printed word bounds.

For a fresh word edit, prepare roughly 15–25 seconds of surrounding music, limited by the actual recording. Store the crop's global origin. The mask sent to Treblo is measured in crop-local seconds. Return the generated patch to the same global location after measuring registration. For a new couplet, a whole uploaded song can supply context; replace only the permitted couplet locally afterward.

## Native generation first

Generate the replacement using Treblo's original-audio conditioning. Start with one representative difficult occurrence and a bounded number of candidates. Preserve the singer/style through source context; supply only the masked words/lines as custom lyrics. Inspect the actual result rather than assuming a seed or successful status establishes correctness.

A subsecond mask was accepted by the API, but first-word consonants required wider masks in some trials. A phrase-sized edit may produce better prosody. Widen only within the user's authorized scope. If an intended word is absent, changing sample rate or declaring the model successful does not fix it.

For a comic insert, preserve the existing setup and place the payoff at a line ending. Count syllables with code, mark stressed vowels, and compare against the sung rhythm. A short, concrete image often works better than an explanatory joke. Preserve as much surrounding text as possible. The worked case changed only two lines in a romantic verse.

## Same-timeline registration and local splice

The provider can re-encode the entire output, even outside the requested mask. Keep the approved master and use the generated file only as a patch source. Compare at least three separate unedited windows; search a small bounded lag range, record the best offsets and confidence, and reject inconsistent lag/drift. Avoid silence and strongly periodic ambiguous windows. Verify the uploaded source itself corresponds to the master before blaming the model.

One observed output had waveform correlations of about 0.63–0.79 with the master outside the edit, while its uploaded source matched at about 0.99. The measured offsets agreed within one sample. This is why audio fidelity and time registration are separate checks. Do not lower a threshold merely to force a pass. If automatic alignment fails, investigate using independent windows, band-limited comparison and listening. Retain that independent evidence when applying a measured lag during preprocessing. The bundled CLI has no manual-lag flag: prepare an explicitly registered same-size donor canvas, as described in [script usage](scripts.md), and then use its zero-offset splice mode.

The provider's output can also be shorter at the end because of codec framing. Never trim the approved master to match it. Require donor coverage of the actual patch and alignment windows; preserve the full master duration.

For each authorized half-open sample interval, blend original and aligned generated samples with a cosine fade that stays entirely inside that interval. Keep every earlier approved patch in a protected interval list and reject overlap. Verify exact PCM equality outside the new mask and within every protected region. Do not rebuild an entire song from separated stems.

## Advanced native-singing donor reconstruction

This branch is optional when native whole-word inpainting cannot retain a usable suffix/melody. It was used in the expanded word-edit task; the later couplet did not require it. Donors must be actual approved generated singing, not TTS or spoken voice-cloning output.

Separate only the needed original and generated contexts with a compatible MelBandRoformer vocal separator. One exercised implementation was the `Separator` class in [YingMusic-Singer-Plus](https://github.com/ASLP-lab/YingMusic-Singer-Plus), under `src/third_party/MusicSourceSeparationTraining/inference_api.py`. Its matched assets were `MelBandRoformer.ckpt` and `config_vocals_mel_band_roformer_kj.yaml` in the [YingMusic-Singer checkpoint directory](https://huggingface.co/ASLP-lab/YingMusic-Singer/tree/main/ckpts). Check current dependencies, model license and asset availability before setup; do not assume an arbitrary similarly named checkpoint matches the config. A free Colab T4 ran the separator with batch size 1, flash attention disabled and AMP disabled. A GPU allocation is not guaranteed.

Measure decoder/separator delay against the original mixture before subtracting vocals. A Demucs experiment had 1,105 leading samples of delay at 48 kHz; this was specific to that decoder and file, never a universal correction. Align the original-vocal estimate to the master first.

Align phonemes in the clean sung donor and target. Crop only the changed prefix when the suffix is shared and already sounds good. Match the donor's duration using RubberBand, with tempo equal to donor-duration divided by target-duration. Preserve formants; change pitch only from measured musical evidence. Pad briefly before processing and remove the corresponding processed padding afterward to avoid transient truncation. Check `ffmpeg -filters` for RubberBand support rather than assuming the installed build has it.

Refine the join by a small bounded sample-lag search near the shared vowel, match local vocal RMS, and optionally match a smoothed envelope with bounded gain. Reconstruct the patch as original mixture plus an in-window fade times the difference between new and aligned original vocal estimates. Keep the original suffix/backing outside that prefix. Validate every occurrence independently; a donor that works in one chorus can fail in a high-pitched final refrain. The portable same-timeline splicer does not automate this phoneme/stem reconstruction branch.

## Lexical and acoustic QA are independent

First ask an audio-capable model or listener to transcribe what is actually sung, without supplying the target lyric. Use complete 15–25-second chorus/verse contexts and then the whole song. Count all requested forms programmatically. Familiar lyrics can bias a transcriber toward the original; isolated syllables can produce unstable guesses. Preserve raw transcripts and uncertainty instead of silently substituting the intended word.

Separately assess voice timbre, rhythm, accompaniment continuity, and seam audibility. A blind comparison should randomize labels and include an identical-audio control. Hashes, not a model's statement, establish byte identity. An auditor once called distinct takes identical; their lexical transcripts still distinguished singular and plural words. Retain such contradictions.

Automated QA is evidence, not an infallible quality score. Do not rerun until a preferred answer appears. A user explicitly approved an all-word version that earlier automated comparisons disliked, and later approved the couplet edit. Preserve that approval alongside the negative reports. If the user asks to hear a disclosed intermediate, deliver it honestly rather than deleting it preemptively.

## Final encoding

Write a FLOAT master and prove finite values, no clipping, rate/channels/frame count, unchanged outside-mask samples and preserved earlier patches. Encode to MP3 (the exercised final used 320 kbps), decode/probe the MP3, and evaluate that encoding. Lossy encoding changes decoded samples, so the exact-preservation claim belongs to the lossless master. Bind all QA evidence to file hashes. Send the checked MP3 bytes without a later unverified re-encode.
