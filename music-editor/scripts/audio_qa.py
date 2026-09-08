#!/usr/bin/env python3
"""Blind direct-audio Gemini QA. No target lyrics, reference text or filename sent."""
import argparse
import base64
import json
import os
from pathlib import Path
import re

import requests

from audio_edit import save, save_json, sha

PROMPTS = {
    "lexical": (
        "Listen directly to the attached audio. Do not infer words from a known song or context. "
        "Return a JSON object with segments (start_seconds, end_seconds, verbatim heard text, "
        "uncertain_words) and limitations. Transcribe all audible singing/speech; mark uncertainty "
        "rather than guessing. Do not use any external transcript."
    ),
    "acoustic": (
        "Listen directly to the attached audio without assuming it was edited. Return a JSON "
        "object with observations (timestamp_seconds, audible evidence, severity), voice_consistency, "
        "rhythm, accompaniment, transitions and limitations. Report concrete audible discontinuities, "
        "if any, and uncertainty. Do not evaluate correctness of lyrics or speculate about production tools."
    ),
}
MIME = {".wav": "audio/wav", ".mp3": "audio/mpeg", ".flac": "audio/flac"}


def parse_result(body):
    if not isinstance(body, dict):
        raise ValueError("QA response envelope must be an object")
    candidates = body.get("candidates", [])
    if (not isinstance(candidates, list) or len(candidates) != 1
            or not isinstance(candidates[0], dict) or candidates[0].get("finishReason") != "STOP"):
        raise ValueError("Missing, multiple, blocked or truncated QA candidate")
    content = candidates[0].get("content")
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list) or any(not isinstance(p, dict) or not isinstance(p.get("text", ""), str) for p in parts):
        raise ValueError("Invalid QA response content parts")
    text = "".join(p.get("text", "") for p in parts if not p.get("thought", False))
    result = json.loads(text)
    if isinstance(result, list) and len(result) == 1:
        result = result[0]
    if not isinstance(result, dict):
        raise ValueError("QA result must be an object or singleton array containing an object")
    # Round-trip also rejects non-JSON NaN/Infinity inside otherwise valid objects.
    json.dumps(result, allow_nan=False)
    return result


def audit(audio, output, model, mode):
    output = Path(output)
    output.mkdir()  # FIRST operation: never pay again or replace earlier evidence.
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", model):
        raise ValueError("Supply an explicit model ID, without a models/ prefix")
    if mode not in PROMPTS:
        raise ValueError("mode must be lexical or acoustic")
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is required")
    audio = Path(audio)
    mime = MIME.get(audio.suffix.lower())
    if mime is None or not 0 < audio.stat().st_size <= 12 * 1024 * 1024:
        raise ValueError("Use a nonempty WAV/MP3/FLAC of at most 12 MiB (inline request budget)")
    data, prompt = audio.read_bytes(), PROMPTS[mode].encode()
    settings = {"temperature": 0, "candidateCount": 1, "responseMimeType": "application/json", "maxOutputTokens": 8192}
    save(output / "prompt.txt", prompt)
    save(output / ("input" + audio.suffix.lower()), data)
    save_json(output / "request.json", dict(model=model, mode=mode, audio_sha256=sha(data),
              audio_bytes=len(data), mime_type=mime, prompt_sha256=sha(prompt), generation_config=settings))
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={"contents": [{"role": "user", "parts": [{"text": prompt.decode()},
              {"inlineData": {"mimeType": mime, "data": base64.b64encode(data).decode()}}]}],
              "generationConfig": settings}, timeout=(15, 180), allow_redirects=False,
    )
    save(output / "raw-response.bin", response.content)
    save_json(output / "response.json", dict(http_status=response.status_code, raw_sha256=sha(response.content)))
    if response.status_code != 200:
        raise ValueError(f"QA HTTP {response.status_code}; raw response retained, no retry")
    result = parse_result(json.loads(response.content))
    save_json(output / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path, help="New immutable-evidence directory; parent must exist")
    parser.add_argument("--model", required=True, help="Explicit Gemini audio-capable model ID")
    parser.add_argument("--mode", choices=PROMPTS, required=True)
    try:
        print(json.dumps(audit(**vars(parser.parse_args())), indent=2))
    except (ValueError, OSError, requests.RequestException) as error:
        parser.exit(1, f"{type(error).__name__}: {error}\n")


if __name__ == "__main__":
    main()
