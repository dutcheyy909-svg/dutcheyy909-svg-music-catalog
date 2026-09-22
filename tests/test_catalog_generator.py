import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "catalog_generator.py"


spec = importlib.util.spec_from_file_location("catalog_generator", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load catalog generator script from {SCRIPT_PATH}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CatalogGeneratorTests(unittest.TestCase):
    def test_build_catalog_uses_repo_relative_sorted_paths_and_skips_output_dirs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "music").mkdir()
            (repo_root / "Output").mkdir()
            (repo_root / "Generated").mkdir()
            (repo_root / "music" / "z-track.wav").write_bytes(b"")
            (repo_root / "music" / "a-track.MP3").write_bytes(b"")
            (repo_root / "Output" / "skip.wav").write_bytes(b"")
            (repo_root / "Generated" / "skip.mp3").write_bytes(b"")
            (repo_root / "catalog.json").write_text("[]", encoding="utf-8")

            catalog = module.build_catalog(repo_root)

            self.assertEqual(
                catalog,
                [
                    {"filename": "a-track.MP3", "path": "music/a-track.MP3"},
                    {"filename": "z-track.wav", "path": "music/z-track.wav"},
                ],
            )

    def test_main_writes_catalog_from_outside_repo_root(self):
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as other_dir:
            repo_root = Path(repo_dir)
            output_path = repo_root / "catalog.json"
            (repo_root / "nested").mkdir()
            (repo_root / "output").mkdir()
            (repo_root / "nested" / "song.wav").write_bytes(b"")
            (repo_root / "output" / "skip.wav").write_bytes(b"")

            original_repo_root = module.REPO_ROOT
            original_output_path = module.OUTPUT_PATH
            original_cwd = Path.cwd()

            try:
                module.REPO_ROOT = repo_root
                module.OUTPUT_PATH = output_path
                os.chdir(other_dir)
                module.main()
            finally:
                os.chdir(original_cwd)
                module.REPO_ROOT = original_repo_root
                module.OUTPUT_PATH = original_output_path

            self.assertEqual(
                json.loads(output_path.read_text(encoding="utf-8")),
                [{"filename": "song.wav", "path": "nested/song.wav"}],
            )


if __name__ == "__main__":
    unittest.main()
