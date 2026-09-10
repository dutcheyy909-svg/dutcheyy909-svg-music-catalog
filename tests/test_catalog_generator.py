import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "catalog_generator.py"


def load_catalog_generator():
    spec = importlib.util.spec_from_file_location("catalog_generator", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CatalogGeneratorTests(unittest.TestCase):
    def test_normalize_reference_path_only_strips_single_dot_prefix(self):
        module = load_catalog_generator()

        self.assertEqual(module._normalize_reference_path("./audio/track.wav"), "audio/track.wav")
        self.assertEqual(module._normalize_reference_path(".hidden/track.wav"), ".hidden/track.wav")
        self.assertIsNone(module._normalize_reference_path("/audio/track.wav"))

    def test_build_catalog_finds_audio_and_enriches_metadata(self):
        module = load_catalog_generator()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "audio").mkdir()
            (root / "metadata").mkdir()
            (root / "audio" / "redline_city.wav").write_bytes(b"wav-data")
            (root / "audio" / "redline_city.mp3").write_bytes(b"mp3-data")
            (root / "metadata" / "redline_city.json").write_text(
                json.dumps(
                    {
                        "title": "Redline City",
                        "composer": "Duncan",
                        "bpm": 134,
                        "genre": "Electronic",
                        "files": {
                            "wav": "audio/redline_city.wav",
                            "mp3": "audio/redline_city.mp3",
                        },
                    }
                ),
                encoding="utf-8",
            )

            catalog = module.build_catalog(root)

            self.assertEqual(
                [track["relative_path"] for track in catalog["tracks"]],
                ["audio/redline_city.mp3", "audio/redline_city.wav"],
            )
            self.assertEqual(
                catalog["tracks"][0]["metadata"],
                {
                    "title": "Redline City",
                    "composer": "Duncan",
                    "genre": "Electronic",
                    "bpm": 134,
                },
            )
            self.assertEqual(
                catalog["tracks"][0]["metadata_sources"],
                ["metadata/redline_city.json"],
            )

    def test_script_writes_stable_catalog_and_ignores_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "nested").mkdir()
            (root / "nested" / "track.wav").write_bytes(b"track-data")
            (root / "notes.txt").write_text("not audio", encoding="utf-8")
            (root / "bad.json").write_text("{not valid json", encoding="utf-8")
            (root / "catalog.json").write_text(
                json.dumps({"tracks": [{"relative_path": "old.wav"}]}),
                encoding="utf-8",
            )

            first_run = subprocess.run(
                [sys.executable, str(MODULE_PATH)],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            second_run = subprocess.run(
                [sys.executable, str(MODULE_PATH)],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            output = (root / "catalog.json").read_text(encoding="utf-8")
            catalog = json.loads(output)

            self.assertIn("Wrote 1 tracks to catalog.json", first_run.stdout)
            self.assertEqual(first_run.stdout, second_run.stdout)
            self.assertEqual(
                catalog,
                {
                    "tracks": [
                        {
                            "filename": "track.wav",
                            "relative_path": "nested/track.wav",
                            "extension": ".wav",
                            "size_bytes": len(b"track-data"),
                        }
                    ]
                },
            )

    def test_catalog_keeps_case_sensitive_files_and_ignores_text_mentions(self):
        module = load_catalog_generator()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "audio").mkdir()
            (root / "metadata").mkdir()
            (root / "audio" / "Song.mp3").write_bytes(b"upper")
            (root / "audio" / "song.mp3").write_bytes(b"lower")
            (root / "metadata" / "song.json").write_text(
                json.dumps(
                    {
                        "title": "Real Song",
                        "file_path": "audio/song.mp3",
                        "description": "Mentioning audio/Song.mp3 here should not create a second match.",
                    }
                ),
                encoding="utf-8",
            )

            catalog = module.build_catalog(root)

            self.assertEqual(
                [track["relative_path"] for track in catalog["tracks"]],
                ["audio/Song.mp3", "audio/song.mp3"],
            )
            self.assertNotIn("metadata", catalog["tracks"][0])
            self.assertEqual(
                catalog["tracks"][1]["metadata"],
                {
                    "title": "Real Song",
                    "description": "Mentioning audio/Song.mp3 here should not create a second match.",
                },
            )


if __name__ == "__main__":
    unittest.main()
