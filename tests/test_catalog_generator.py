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
    def test_build_catalog_uses_repo_relative_sorted_paths_and_skips_generated_dirs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "alpha").mkdir()
            (repo_root / "Output").mkdir()
            (repo_root / "Generated").mkdir()
            (repo_root / "build").mkdir()
            (repo_root / "Dist").mkdir()
            (repo_root / "node_modules").mkdir()
            (repo_root / "__PYCACHE__").mkdir()
            (repo_root / "zeta").mkdir()
            (repo_root / "alpha" / "a-track.MP3").write_bytes(b"")
            (repo_root / "zeta" / "z-track.wav").write_bytes(b"")
            (repo_root / "Output" / "skip.wav").write_bytes(b"")
            (repo_root / "Generated" / "skip.mp3").write_bytes(b"")
            (repo_root / "build" / "skip.wav").write_bytes(b"")
            (repo_root / "Dist" / "skip.wav").write_bytes(b"")
            (repo_root / "node_modules" / "skip.wav").write_bytes(b"")
            (repo_root / "__PYCACHE__" / "skip.wav").write_bytes(b"")
            (repo_root / "catalog.json").write_text("[]", encoding="utf-8")

            catalog = module.build_catalog(repo_root)

            self.assertEqual(
                catalog,
                [
                    {"filename": "a-track.MP3", "path": "alpha/a-track.MP3"},
                    {"filename": "z-track.wav", "path": "zeta/z-track.wav"},
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

    def test_write_catalog_emits_valid_json_with_trailing_newline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "catalog.json"
            catalog = [{"filename": "song.wav", "path": "nested/song.wav"}]

            module.write_catalog(catalog, output_path)

            written = output_path.read_text(encoding="utf-8")
            self.assertTrue(written.endswith("\n"))
            self.assertEqual(json.loads(written), catalog)


if __name__ == "__main__":
    unittest.main()
