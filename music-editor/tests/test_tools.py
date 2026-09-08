"""All audio here is deterministic SYNTHETIC noise/tones, never real recordings."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load(name):
    path = ROOT / "scripts" / f"{name}.py"
    assert path.is_file(), f"Missing implementation: {path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.audio = load("audio_edit")
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / "tests")
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        self.rate = 16000
        self.x = np.random.default_rng(420).uniform(-0.2, 0.2, (32000, 2)).astype("float32")
        self.y = self.x.copy()
        self.y[12000:14000] *= -1
        self.master, self.donor = self.d / "master.wav", self.d / "donor.wav"
        sf.write(self.master, self.x, self.rate, subtype="FLOAT")
        sf.write(self.donor, self.y, self.rate, subtype="FLOAT")

    def splice(self, **kw):
        args = dict(master=self.master, generated=self.donor, output=self.d / "render",
                    edits=[(12000, 14000)], fade=100, expected_count=1,
                    protected=[(100, 1000)])
        args.update(kw)
        return self.audio.splice(**args)

    def test_splice_proof_mp3_and_immutable_source(self):
        original = self.master.read_bytes()
        proof = self.splice()
        out, rate = sf.read(self.d / "render/edited.wav", dtype="float32", always_2d=True)
        self.assertEqual(rate, self.rate)
        np.testing.assert_array_equal(out[:12000], self.x[:12000])
        np.testing.assert_array_equal(out[14000:], self.x[14000:])
        np.testing.assert_array_equal(out[12000], self.x[12000])
        np.testing.assert_array_equal(out[13999], self.x[13999])
        np.testing.assert_array_equal(out[12100:13900], self.y[12100:13900])
        self.assertEqual(self.master.read_bytes(), original)
        self.assertTrue(proof["outside_equal"])
        self.assertTrue(proof["protected"][0]["equal"])
        self.assertEqual(proof["frames"], len(self.x))
        self.assertEqual(proof["hashes"]["mp3"], hashlib.sha256((self.d / "render/edited.mp3").read_bytes()).hexdigest())
        self.assertEqual(json.loads((self.d / "render/proof.json").read_text()), proof)
        self.assertFalse(proof["mp3_sample_identity_claimed"])
        decoded = subprocess.run(["ffmpeg", "-v", "error", "-i", str(self.d / "render/edited.mp3"),
                                  "-f", "f32le", "-"], capture_output=True, check=True)
        self.assertGreater(len(decoded.stdout), 0)
        with self.assertRaises(FileExistsError):
            self.splice()

    def test_decode_native_rate_channels_and_no_overwrite_cli(self):
        source = self.d / "native.wav"
        sf.write(source, self.x[:, :1], 22050, subtype="PCM_16")
        cmd = [sys.executable, str(ROOT / "scripts/audio_edit.py"), "decode", str(source), str(self.d / "decoded")]
        subprocess.run(cmd, check=True, capture_output=True)
        info = sf.info(self.d / "decoded/master.wav")
        self.assertEqual((info.samplerate, info.channels, info.frames, info.subtype), (22050, 1, len(self.x), "FLOAT"))
        self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_cli_splice(self):
        cmd = [sys.executable, str(ROOT / "scripts/audio_edit.py"), "splice", str(self.master), str(self.donor),
               str(self.d / "cli"), "--edit", "12000:14000", "--fade-samples", "100", "--expected-count", "1",
               "--protect", "100:1000"]
        subprocess.run(cmd, check=True, capture_output=True)
        self.assertTrue(json.loads((self.d / "cli/proof.json").read_text())["outside_equal"])

    def test_invalid_intervals_counts_and_fades(self):
        for args in [dict(edits=[(-1, 100)]), dict(edits=[(10, 10)]), dict(edits=[(0, 32001)]),
                     dict(edits=[(12000, 14000), (13000, 15000)], expected_count=2),
                     dict(edits=[(12000, 14000), (12000, 14000)], expected_count=2),
                     dict(edits=[]), dict(expected_count=2), dict(expected_count=0), dict(fade=1001),
                     dict(fade=-1), dict(fade=1), dict(protected=[(13000, 15000)]),
                     dict(protected=[(0, 500), (400, 600)]), dict(edits=[(1.5, 200)])]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.splice(**args)

    def test_invalid_audio(self):
        for data, rate in [(self.y[:-1], self.rate), (self.y[:, :1], self.rate), (self.y, 22050),
                           (np.full_like(self.y, np.nan), self.rate), (np.full_like(self.y, np.inf), self.rate),
                           (np.full_like(self.y, 1.1), self.rate), (np.ones_like(self.y), self.rate)]:
            sf.write(self.donor, data, rate, subtype="FLOAT")
            with self.subTest(shape=data.shape, rate=rate), self.assertRaises(ValueError):
                self.splice()
        sf.write(self.master, self.x, self.rate, subtype="PCM_16")
        with self.assertRaises(ValueError):
            self.splice()

    def test_measured_positive_and_negative_lag(self):
        windows = [(1000, 3000), (4000, 6000), (22000, 24000)]
        for lag in [7, -9, 0]:
            y = np.zeros_like(self.y)
            if lag > 0:
                y[lag:] = self.y[:-lag]
            elif lag < 0:
                y[:lag] = self.y[-lag:]
            else:
                y[:] = self.y
            sf.write(self.donor, y, self.rate, subtype="FLOAT")
            proof = self.splice(output=self.d / f"lag{lag}", windows=windows, max_lag=20)
            self.assertEqual(proof["alignment"]["lag_samples"], lag)
            self.assertEqual(len(proof["alignment"]["measurements"]), 3)
            out, _ = sf.read(self.d / f"lag{lag}/edited.wav", dtype="float32", always_2d=True)
            np.testing.assert_array_equal(out[12100:13900], self.y[12100:13900])

    def test_alignment_refuses_bad_windows_or_unreliable_signal(self):
        for windows in [[(1000, 3000)], [(1000, 3000)] * 3,
                        [(1000, 3000), (4000, 6000), (12000, 14000)],
                        [(0, 1000), (4000, 6000), (22000, 24000)]]:
            with self.subTest(windows=windows), self.assertRaises(ValueError):
                self.splice(windows=windows, max_lag=20)
        sf.write(self.donor, np.zeros_like(self.y), self.rate, subtype="FLOAT")
        with self.assertRaises(ValueError):
            self.splice(windows=[(1000, 3000), (4000, 6000), (22000, 24000)], max_lag=20)

    def test_multiple_edits_zero_fade_and_protected_regions(self):
        proof = self.splice(edits=[(12000, 12500), (13500, 14000)], expected_count=2, fade=0,
                            protected=[(100, 1000), (12500, 13500)])
        out, _ = sf.read(self.d / "render/edited.wav", dtype="float32", always_2d=True)
        np.testing.assert_array_equal(out[12000:12500], self.y[12000:12500])
        np.testing.assert_array_equal(out[12500:13500], self.x[12500:13500])
        self.assertEqual(proof["edit_count"], 2)
        self.assertTrue(all(p["equal"] for p in proof["protected"]))

    def test_inconsistent_and_periodic_alignment_rejected(self):
        windows = [(1000, 3000), (4000, 6000), (22000, 24000)]
        y = self.y.copy()
        y[22000:24000] = self.x[21990:23990]
        sf.write(self.donor, y, self.rate, subtype="FLOAT")
        with self.assertRaisesRegex(ValueError, "Inconsistent"):
            self.splice(windows=windows, max_lag=20)
        periodic = np.tile(np.array([0.1, -0.1], dtype="float32"), len(self.x)//2)
        sf.write(self.master, periodic, self.rate, subtype="FLOAT")
        sf.write(self.donor, periodic, self.rate, subtype="FLOAT")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.splice(windows=windows, max_lag=20)

    def test_decode_mp3_and_multichannel_wav(self):
        mp3 = self.d / "synthetic.mp3"
        subprocess.run(["ffmpeg", "-v", "error", "-n", "-i", str(self.master), "-c:a", "libmp3lame", str(mp3)], check=True)
        self.audio.decode(mp3, self.d / "decoded-mp3")
        info = sf.info(self.d / "decoded-mp3/master.wav")
        self.assertEqual((info.samplerate, info.channels, info.frames, info.subtype), (self.rate, 2, len(self.x), "FLOAT"))
        source = self.d / "surround.wav"
        sf.write(source, np.tile(self.x, (1, 2)), 32000, subtype="PCM_16")
        self.audio.decode(source, self.d / "decoded-surround")
        info = sf.info(self.d / "decoded-surround/master.wav")
        self.assertEqual((info.samplerate, info.channels, info.frames, info.subtype), (32000, 4, len(self.x), "FLOAT"))

    def test_no_overwrites_of_input_or_existing_directory(self):
        original = self.master.read_bytes()
        with self.assertRaises(FileExistsError):
            self.splice(output=self.master)
        self.assertEqual(original, self.master.read_bytes())
        (self.d / "render").mkdir()
        marker = self.d / "render/proof.json"
        marker.write_text("existing evidence")
        with self.assertRaises(FileExistsError):
            self.splice()
        self.assertEqual(marker.read_text(), "existing evidence")


class QATests(unittest.TestCase):
    def setUp(self):
        self.qa = load("audio_qa")
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / "tests")
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        self.audio = self.d / "synthetic.wav"
        sf.write(self.audio, np.zeros(800, dtype="float32"), 8000, subtype="FLOAT")

    def response(self, value):
        # Explicit transport fake: never network/model output represented as real QA.
        body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(value)}]}}]}
        response = Mock(status_code=200, content=json.dumps(body).encode())
        return response

    def run_qa(self, **kwargs):
        args = dict(audio=self.audio, output=self.d / "qa", model="test-model", mode="acoustic")
        args.update(kwargs)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "synthetic-test-key"}):
            return self.qa.audit(**args)

    def test_object_and_singleton_array_preserved_evidence(self):
        for index, value in enumerate([{"observations": "synthetic fake"}, [{"observations": "synthetic fake"}]]):
            with patch.object(self.qa.requests, "post", return_value=self.response(value)) as post:
                result = self.run_qa(output=self.d / str(index))
            self.assertEqual(result, {"observations": "synthetic fake"})
            directory = self.d / str(index)
            manifest = json.loads((directory / "request.json").read_text())
            self.assertEqual(manifest["audio_sha256"], hashlib.sha256(self.audio.read_bytes()).hexdigest())
            self.assertEqual(manifest["prompt_sha256"], hashlib.sha256((directory / "prompt.txt").read_bytes()).hexdigest())
            self.assertEqual((directory / "raw-response.bin").read_bytes(), self.response(value).content)
            payload = post.call_args.kwargs["json"]
            self.assertEqual(payload["contents"][0]["parts"][0]["text"], self.qa.PROMPTS["acoustic"])
            self.assertNotIn("synthetic.wav", json.dumps(payload))
            self.assertNotIn("key=", post.call_args.args[0])
            self.assertEqual(post.call_args.kwargs["headers"]["x-goog-api-key"], "synthetic-test-key")

    def test_existing_output_means_no_network_even_missing_input(self):
        (self.d / "qa").mkdir()
        with patch.object(self.qa.requests, "post") as post, self.assertRaises(FileExistsError):
            self.run_qa(audio=self.d / "absent.wav")
        post.assert_not_called()

    def test_malformed_shapes_keep_raw_and_block_retry(self):
        for index, value in enumerate([[], [{}, {}], "text", None, 4, [3]]):
            directory = self.d / str(index)
            with patch.object(self.qa.requests, "post", return_value=self.response(value)), self.assertRaises(ValueError):
                self.run_qa(output=directory)
            self.assertTrue((directory / "raw-response.bin").is_file())
            self.assertFalse((directory / "result.json").exists())
            with patch.object(self.qa.requests, "post") as post, self.assertRaises(FileExistsError):
                self.run_qa(output=directory)
            post.assert_not_called()

    def test_network_failure_preserves_prompt(self):
        with patch.object(self.qa.requests, "post", side_effect=self.qa.requests.Timeout("synthetic timeout")), self.assertRaises(self.qa.requests.Timeout):
            self.run_qa()
        self.assertTrue((self.d / "qa/prompt.txt").is_file())
        self.assertTrue((self.d / "qa/request.json").is_file())

    def test_http_error_preserves_raw(self):
        response = Mock(status_code=429, content=b'{"error":"synthetic quota failure"}')
        with patch.object(self.qa.requests, "post", return_value=response), self.assertRaises(ValueError):
            self.run_qa()
        self.assertEqual((self.d / "qa/raw-response.bin").read_bytes(), response.content)

    def test_model_required_cli(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/audio_qa.py"), str(self.audio), str(self.d / "qa")], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"--model", result.stderr)

    def test_invalid_envelopes_and_nonfinite_json_preserve_raw(self):
        for index, body in enumerate([[], {}, {"candidates": []},
                                     {"candidates": [{"finishReason": "MAX_TOKENS"}]},
                                     {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '{"a": NaN}'}]}}]}]):
            response = Mock(status_code=200, content=json.dumps(body).encode())
            directory = self.d / str(index)
            with patch.object(self.qa.requests, "post", return_value=response), self.assertRaises(ValueError):
                self.run_qa(output=directory)
            self.assertEqual((directory / "raw-response.bin").read_bytes(), response.content)

    def test_bad_model_and_missing_key_never_network(self):
        for index, model in enumerate(["", "models/test", "test?key=foo", " test"]):
            with patch.object(self.qa.requests, "post") as post, self.assertRaises(ValueError):
                self.run_qa(output=self.d / str(index), model=model)
            post.assert_not_called()
        with patch.dict(os.environ, {}, clear=True), patch.object(self.qa.requests, "post") as post, self.assertRaises(ValueError):
            self.qa.audit(self.audio, self.d / "nokey", "test-model", "lexical")
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
