# Portable audio utilities

Python 3.11+, NumPy, SciPy, SoundFile/libsndfile, Requests, and `ffmpeg` with the `libmp3lame` encoder. No personal helpers, generation services, GPU, or private assets are required. Run these examples from the repository root:

```sh
python -m pip install -r music-editor/requirements.txt
python music-editor/scripts/audio_edit.py --help
python music-editor/scripts/audio_qa.py --help
python -m unittest discover -s music-editor/tests -v
```

The tests create **explicitly synthetic** seeded noise/tones in temporary directories under `tests/`, then remove them. FFmpeg decoding, rendering, and MP3 decoding run for real. QA transport is mocked with explicitly synthetic responses: the suite makes **no network requests**, incurs no charges, and does not establish any live model's availability or listening quality.

## 1. Decode once; preserve the master

```sh
python music-editor/scripts/audio_edit.py decode input.mp3 decoded-v1
```

Creates `decoded-v1/master.wav` and `decoded-v1/proof.json`. The output directory must not exist, and its parent must exist. Decodes the first audio stream with FFmpeg into **32-bit FLOAT WAV**, preserving its native decoded sample rate and channel count (no `-ar`, `-ac`, normalization, or gain changes). Container metadata is stripped. Source and master SHA-256, sample count/rate/channels/subtype and peak are recorded. Source bytes are checked again before success.

All decoded audio must be nonempty and finite, with `abs(sample) < 1`. Full-scale samples, clipping, NaN and Infinity cause failure rather than silent limiting. A source already at full scale therefore needs an explicit, separately authorized preparation decision; this tool does not alter it automatically.

## 2. Splice only explicit intervals

The generated input must be an already available **complete same-timeline recording**, matching master frame count, rate and channels exactly. Raw Treblo downloads can differ in rate or tail length, so they may not satisfy this utility's input contract directly. For that case, independently measure the time registration as described in [editing-and-qa.md](editing-and-qa.md), convert only the donor to the master's rate/channels, and create an explicit same-size donor canvas: copy the master, then insert the measured, aligned donor samples only into the intended patch interval. Record the original donor hash, conversion, measured offset and canvas construction in private provenance. Pass this already registered canvas with no automatic alignment windows. Never trim the approved master or invent missing donor content to satisfy the shape check. The tool does not generate vocals, stretch, resample, pad, truncate, infer word boundaries, separate stems, or modify the master. For sample-exact protection the master must be FLOAT WAV; decode integer-PCM sources first. Rendering currently accepts mono/stereo only because it always makes an MP3; multichannel decoding is supported, but rendering never silently downmixes.

Every interval is `START:END` in **integer sample frames**, zero-based and half-open: start included, end excluded. A frame includes all channels. Convert time boundaries to sample indices deliberately before invocation; no seconds-to-samples rounding is hidden in the CLI. The numbers below are illustrative, not recommended word boundaries:

```sh
python music-editor/scripts/audio_edit.py splice \
  decoded-v1/master.wav generated-same-timeline.wav render-v1 \
  --edit 48000:60000 --edit 192000:204000 \
  --expected-count 2 --fade-samples 480 \
  --protect 120000:144000
```

- `--edit` is repeatable and required; `--expected-count` must equal the positive number of intervals. This checks **configured edit count**, not lyric correctness or the number of heard words.
- `--protect` is repeatable. Protected intervals must be in bounds, nonempty, nonoverlapping and disjoint from edits. All other out-of-edit samples are also protected implicitly.
- Edits must be in bounds, nonempty and nonoverlapping; adjacent intervals are allowed. Sorting does not change their indices.
- `--fade-samples` is required: `0` means a hard splice; otherwise it must be at least `2`, and twice its length must fit inside every interval. The raised-cosine weight goes from original-only at the first frame to generated-only, with the reverse ramp at the end. **Fades never extend outside edit bounds.** A hard splice can click; numerical validity is not acoustic acceptance.
- Inputs and output must be finite and below full scale. No clipping repair, normalization, or gain matching occurs.

### Optional measured global lag

Without alignment windows, the offset is exactly zero; there is no guessed or hard-coded correction. To measure one constant offset, add at least **three distinct, nonoverlapping, explicitly unedited windows**:

```sh
python music-editor/scripts/audio_edit.py splice \
  decoded-v1/master.wav generated-same-timeline.wav render-aligned-v1 \
  --edit 48000:60000 --edit 192000:204000 \
  --expected-count 2 --fade-samples 480 \
  --protect 120000:144000 \
  --align-window 6000:18000 \
  --align-window 96000:108000 \
  --align-window 240000:252000 \
  --max-lag-samples 960
```

Use windows spread through the recording. Each window **plus the search margin on both sides** must fit in the recording and not intersect an edit. The default search radius is `2400` samples; it applies only when windows are supplied. This is a limit, not an assumed offset.

Per-channel mean-centered, normalized cross-correlation is aggregated across channels. Each window must have correlation at least `0.8`, a winning-peak margin of at least `0.02` over candidates more than one sample away, and no winning peak on the search boundary. Silent, weak, ambiguous/periodic or inconsistent windows fail closed. The measured offsets must span at most one sample. The integer-truncated median offset is applied only while extracting the donor patches; positive lag means the generated recording is delayed, so master frame `i` uses donor frame `i + lag`. Shifted patches must still fit; no edge padding is invented. The JSON records every window, score and offset. A single global lag cannot correct tempo drift, local timing changes or a bad donor.

### Output and proof

A successful new render directory contains:

- `edited.wav`: FLOAT WAV with unchanged frame count, native rate and channels.
- `edited.mp3`: `libmp3lame -q:a 2` listening/delivery derivative, also exercised through FFmpeg's decoder.
- `proof.json`: input/output file SHA-256s, interval/count/fade settings, alignment evidence, peak, a read-back `outside_equal` assertion, outside-PCM SHA-256, and equality/hash evidence for every protected interval. PCM hashes use interleaved little-endian float32 samples. Input hashes are rechecked after rendering.

The saved WAV is read back and compared to the master before success. **PCM sample identity applies to the WAV only.** MP3 encoding is lossy, may choose a supported MP3 rate for unusual source rates, may introduce overshoot, and cannot preserve decoded sample identity. MP3 SHA-256 binds the delivery bytes, not a claim of unchanged decoded samples; `mp3_sample_identity_claimed` is explicitly false. This proof establishes numerical preservation, not lyric accuracy, singer identity, or inaudible transitions.

## 3. Separate blind direct-audio QA

This command **uploads audio to Google's Gemini API and may incur charges**. Run it only with rights/consent and authorization to use that service and budget. Set `GEMINI_API_KEY` securely in the environment; never put a key in a command argument, source file, evidence, or public repository. Select an available audio-capable model explicitly; no model ID, account entitlement, or price is assumed here.

```sh
python music-editor/scripts/audio_qa.py render-v1/edited.mp3 qa-lexical-v1 \
  --model YOUR_AUDIO_CAPABLE_GEMINI_MODEL_ID --mode lexical
python music-editor/scripts/audio_qa.py render-v1/edited.mp3 qa-acoustic-v1 \
  --model YOUR_AUDIO_CAPABLE_GEMINI_MODEL_ID --mode acoustic
```

`--model` and `--mode` are required. Supply the model ID literally, without a `models/` prefix; malformed IDs are rejected, not normalized. Modes use fixed, separate blind prompts: lexical asks for directly heard words/timestamps/uncertainty; acoustic asks for audible voice/rhythm/backing/transition evidence without evaluating target words. Neither receives a target lyric, reference transcript, user filename or prior verdict. Embedded input-container metadata is not scrubbed by QA; use metadata-free inputs if metadata could reveal the answer. These prompts reduce textual priming but cannot prevent a model from guessing or hallucinating.

Accepted inputs are nonempty WAV, MP3 or FLAC, at most **12 MiB** to leave room for base64/JSON within an inline request. Larger recordings need separately planned contextual excerpts; do not quietly substitute a short clip for a whole-recording check. The exact original audio bytes are sent inline, not a transcript. No upload/file-management service or generation endpoint is used.

Each invocation exclusively creates a new evidence directory **before any network operation**, storing:

- `input.wav` / `input.mp3` / `input.flac`: the exact submitted bytes.
- `prompt.txt`: exact fixed prompt bytes.
- `request.json`: explicit model, mode, audio SHA-256/size/MIME, prompt SHA-256 and generation settings.
- `raw-response.bin`: exact HTTP response body, including failed/invalid responses when received.
- `response.json`: HTTP status and raw-response SHA-256.
- `result.json`: validated model JSON, created only after successful validation.

The parser accepts a JSON object or unwraps exactly one object inside a singleton array. It rejects other shapes, nonfinite JSON values, missing/multiple candidates, blocked responses and non-`STOP` finishes (including truncation). It does **not** assert semantic completeness of the object's fields or turn a verdict into human acceptance. Model reasoning/thought parts are ignored during parsing but retained in the raw response. Preserve contradictory results; do not rerun until a pass or overwrite a failed audit.

There are no automatic retries or redirects. Transport timeouts leave the submitted prompt/input/request evidence; no raw output can be saved if no response arrived. If **any output path already exists**, even an empty/failed directory, the command refuses before touching the input or making a request. Evidence is write-once by these utilities, not filesystem WORM protection. A deliberate new audit requires a deliberate new directory.

## Failure and operational limits

All output directories are exclusive reservations, and files are created without overwrite. A partial directory may remain after an error and is intentionally not reused; inspect it, retain relevant evidence, and choose a new path for an authorized new attempt. Existing inputs/evidence are never deleted. A success `proof.json` or QA `result.json` is written last. Input/output arrays and audio snapshots are loaded into memory; these compact utilities are intended for ordinary song-length recordings, not unbounded streaming. Do not concurrently modify inputs or the newly reserved output directory.
