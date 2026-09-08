#!/usr/bin/env python3
"""Exact-window FLOAT-WAV editing; all bounds are half-open sample indices."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import correlate


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    with Path(path).open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def save_json(path, value):
    save(path, (json.dumps(value, indent=2, allow_nan=False) + "\n").encode())


def check_audio(data):
    if not data.size or not np.isfinite(data).all():
        raise ValueError("Empty or nonfinite audio")
    if np.max(np.abs(data)) >= 1:
        raise ValueError("Full-scale/clipped audio: abs(sample) must be < 1; no automatic limiting")


def read_audio(path):
    raw = Path(path).read_bytes()
    with sf.SoundFile(io.BytesIO(raw)) as handle:
        info = (handle.samplerate, handle.channels, handle.subtype, handle.format)
        data = handle.read(dtype="float32", always_2d=True)
    check_audio(data)
    return data, info, sha(raw)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n", *map(str, args)], check=True)


def decode(source, output):
    output = Path(output)
    output.mkdir()  # Exclusive reservation, including failed/partial previous runs.
    before = sha(Path(source).read_bytes())
    ffmpeg("-i", source, "-map", "0:a:0", "-map_metadata", "-1", "-c:a", "pcm_f32le", output / "master.wav")
    data, info, digest = read_audio(output / "master.wav")
    if sha(Path(source).read_bytes()) != before:
        raise ValueError("Source changed during decoding")
    proof = dict(source_sha256=before, master_sha256=digest, sample_rate=info[0],
                 channels=info[1], frames=len(data), subtype=info[2], peak=float(np.abs(data).max()))
    save_json(output / "proof.json", proof)
    return proof


def intervals(values, frames):
    result = []
    for pair in values:
        if len(pair) != 2 or any(type(n) is not int for n in pair):
            raise ValueError("Intervals require two integer sample indices")
        a, b = pair
        if not 0 <= a < b <= frames:
            raise ValueError("Interval outside audio or empty")
        result.append((a, b))
    result.sort()
    if any(left[1] > right[0] for left, right in zip(result, result[1:])):
        raise ValueError("Overlapping or duplicate intervals")
    return result


def overlaps(left, right):
    return any(a < d and c < b for a, b in left for c, d in right)


def measure_lag(master, donor, windows, edits, max_lag):
    if type(max_lag) is not int or max_lag < 1:
        raise ValueError("max_lag must be a positive integer")
    windows = intervals(windows, len(master))
    if len(windows) < 3:
        raise ValueError("Alignment requires at least three distinct unedited windows")
    measurements = []
    for a, b in windows:
        if a < max_lag or b + max_lag > len(donor) or overlaps([(a-max_lag, b+max_lag)], edits):
            raise ValueError("Alignment windows plus search margin must be in bounds and unedited")
        ref = master[a:b].astype("float64")
        ref -= ref.mean(axis=0)
        ext = donor[a-max_lag:b+max_lag].astype("float64")
        n = b-a
        numerator = sum(correlate(ext[:, c], ref[:, c], mode="valid", method="fft") for c in range(ref.shape[1]))
        sums = np.vstack([np.zeros((1, ext.shape[1])), np.cumsum(ext, axis=0)])
        squares = np.vstack([np.zeros((1, ext.shape[1])), np.cumsum(ext*ext, axis=0)])
        energy = np.maximum(0, (squares[n:]-squares[:-n] - (sums[n:]-sums[:-n])**2/n).sum(axis=1))
        denom = np.sqrt(energy * np.sum(ref*ref))
        scores = np.divide(numerator, denom, out=np.full_like(denom, -1), where=denom > 1e-12)
        peak = int(np.argmax(scores))
        rivals = scores.copy()
        rivals[max(0, peak-1):peak+2] = -1
        if scores[peak] < 0.8 or scores[peak]-rivals.max() < 0.02 or peak in (0, len(scores)-1):
            raise ValueError("Weak/ambiguous lag correlation or search-edge peak")
        measurements.append(dict(window=[a, b], lag_samples=peak-max_lag, correlation=float(scores[peak])))
    lags = [m["lag_samples"] for m in measurements]
    if max(lags)-min(lags) > 1:
        raise ValueError("Inconsistent lag across windows; global alignment unsafe")
    return dict(lag_samples=int(np.median(lags)), measurements=measurements)


def splice(master, generated, output, edits, fade, expected_count, protected=(), windows=(), max_lag=2400):
    output = Path(output)
    if os.path.lexists(output):
        raise FileExistsError(output)
    x, info, master_hash = read_audio(master)
    y, donor_info, donor_hash = read_audio(generated)
    if info[2:] != ("FLOAT", "WAV"):
        raise ValueError("Master must be a FLOAT WAV from decode (avoids quantization outside edits)")
    if x.shape != y.shape or info[:2] != donor_info[:2]:
        raise ValueError("Generated recording must match master frame count, rate and channels")
    if info[1] > 2:
        raise ValueError("MP3 rendering supports mono/stereo only; no implicit downmix")
    edits, protected = intervals(edits, len(x)), intervals(protected, len(x))
    if type(expected_count) is not int or expected_count < 1 or len(edits) != expected_count:
        raise ValueError("Edit count must match explicit positive expected_count")
    if type(fade) is not int or fade < 0 or fade == 1 or any(2*fade > b-a for a, b in edits):
        raise ValueError("Fade must be zero or >=2 samples, and fit twice inside each edit")
    if overlaps(edits, protected):
        raise ValueError("Edit intersects protected interval")
    alignment = measure_lag(x, y, windows, edits, max_lag) if windows else dict(lag_samples=0, measurements=[])
    lag = alignment["lag_samples"]
    result, mask = x.copy(), np.zeros(len(x), dtype=bool)
    for a, b in edits:
        if a+lag < 0 or b+lag > len(y):
            raise ValueError("Aligned donor does not cover edit")
        weights = np.ones(b-a, dtype="float64")
        if fade:
            ramp = (1-np.cos(np.linspace(0, np.pi, fade)))/2
            weights[:fade], weights[-fade:] = ramp, ramp[::-1]
        result[a:b] = (x[a:b].astype("float64")*(1-weights[:, None]) + y[a+lag:b+lag]*weights[:, None]).astype("float32")
        mask[a:b] = True
    check_audio(result)
    output.mkdir()
    with (output / "edited.wav").open("xb") as handle:
        sf.write(handle, result, info[0], subtype="FLOAT", format="WAV")
    actual, actual_info, wav_hash = read_audio(output / "edited.wav")
    outside_equal = np.array_equal(x[~mask], actual[~mask])
    protected_proof = [dict(interval=[a, b], equal=np.array_equal(x[a:b], actual[a:b]),
                            pcm_sha256=sha(actual[a:b].astype("<f4").tobytes())) for a, b in protected]
    if actual.shape != x.shape or actual_info != info or not outside_equal or not all(p["equal"] for p in protected_proof):
        raise ValueError("Written WAV failed preservation proof")
    ffmpeg("-i", output / "edited.wav", "-map_metadata", "-1", "-c:a", "libmp3lame", "-q:a", "2", output / "edited.mp3")
    ffmpeg("-i", output / "edited.mp3", "-f", "null", "-")  # Exercise decoder too.
    if sha(Path(master).read_bytes()) != master_hash or sha(Path(generated).read_bytes()) != donor_hash:
        raise ValueError("Input changed during render")
    proof = dict(sample_rate=info[0], channels=info[1], frames=len(actual), edits=[list(p) for p in edits],
                 edit_count=len(edits), fade_samples=fade, alignment=alignment, outside_equal=outside_equal,
                 outside_pcm_sha256=sha(actual[~mask].astype("<f4").tobytes()), protected=protected_proof,
                 peak=float(np.abs(actual).max()), mp3_sample_identity_claimed=False,
                 hashes=dict(master=master_hash, generated=donor_hash, wav=wav_hash,
                             mp3=sha((output / "edited.mp3").read_bytes())))
    save_json(output / "proof.json", proof)
    return proof


def pair(text):
    try:
        a, b = text.split(":")
        return int(a), int(b)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Use START:END integer sample indices") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    dec = sub.add_parser("decode", help="Decode first audio stream at native rate/channels to FLOAT WAV")
    dec.add_argument("source", type=Path)
    dec.add_argument("output", type=Path, help="New output directory (parent must exist)")
    edit = sub.add_parser("splice", help="Splice same-timeline recording into immutable FLOAT master")
    for name in ("master", "generated", "output"):
        edit.add_argument(name, type=Path)
    edit.add_argument("--edit", type=pair, action="append", required=True, dest="edits")
    edit.add_argument("--protect", type=pair, action="append", default=[], dest="protected")
    edit.add_argument("--align-window", type=pair, action="append", default=[], dest="windows")
    edit.add_argument("--max-lag-samples", type=int, default=2400, dest="max_lag")
    edit.add_argument("--fade-samples", type=int, required=True, dest="fade")
    edit.add_argument("--expected-count", type=int, required=True)
    args = vars(parser.parse_args())
    command = args.pop("command")
    try:
        print(json.dumps(decode(**args) if command == "decode" else splice(**args), indent=2))
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{type(error).__name__}: {error}\n")


if __name__ == "__main__":
    main()
