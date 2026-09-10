import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "catalog_generator.py"
SPEC = importlib.util.spec_from_file_location("catalog_generator", MODULE_PATH)
catalog_generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog_generator)


class CatalogGeneratorTests(unittest.TestCase):
    def test_build_catalog_lists_audio_files_with_stable_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            repository_root = Path(temp_directory)
            (repository_root / "music" / "album").mkdir(parents=True)
            (repository_root / ".git").mkdir()
            (repository_root / ".github" / "workflows").mkdir(parents=True)
            (repository_root / "node_modules" / "demo").mkdir(parents=True)

            ignored_output = repository_root / "catalog.mp3"
            (repository_root / "music" / "album" / "anthem.MP3").write_bytes(b"upper-mp3")
            (repository_root / "music" / "album" / "beat.WAV").write_bytes(b"upper-wav")
            (repository_root / "music" / "album" / "track.wav").write_bytes(b"wav")
            (repository_root / "music" / "album" / "track.mp3").write_bytes(b"mp3")
            ignored_output.write_bytes(b"generated-audio")
            (repository_root / "music" / "album" / "notes.txt").write_text("ignore", encoding="utf-8")
            (repository_root / ".git" / "ignored.wav").write_bytes(b"git")
            (repository_root / ".github" / "workflows" / "ignored.mp3").write_bytes(b"github")
            (repository_root / "node_modules" / "demo" / "ignored.mp3").write_bytes(b"node")

            catalog = catalog_generator.build_catalog(
                repository_root, ignored_paths={ignored_output}
            )

        self.assertEqual(
            catalog,
            [
                {"filename": "anthem.MP3", "path": "music/album/anthem.MP3"},
                {"filename": "beat.WAV", "path": "music/album/beat.WAV"},
                {"filename": "track.mp3", "path": "music/album/track.mp3"},
                {"filename": "track.wav", "path": "music/album/track.wav"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
