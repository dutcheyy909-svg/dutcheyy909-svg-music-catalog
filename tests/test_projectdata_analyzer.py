import importlib
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
analyzer = importlib.import_module("projectdata_analyzer")
extractor = importlib.import_module("projectdata_extractor")


class ProjectDataAnalyzerTests(unittest.TestCase):
    def test_root_requirements_cover_runtime_and_test_dependencies(self):
        requirement_lines = {
            line.split("#", 1)[0].strip()
            for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
            if line.split("#", 1)[0].strip() and not line.split("#", 1)[0].strip().startswith("-")
        }

        self.assertTrue(
            {
                "librosa==0.10.0",
                "numpy>=1.26,<2",
                "pytest>=8,<9",
                "PyYAML>=6,<7",
            }.issubset(requirement_lines)
        )

    def test_extractor_is_compatibility_wrapper_for_analyzer(self):
        self.assertTrue(set(analyzer.__all__).issubset(extractor.__all__))
        self.assertTrue({"csv", "json", "librosa", "np", "Path"}.issubset(extractor.__all__))
        self.assertIs(extractor.generate_sync_tags, analyzer.generate_sync_tags)
        self.assertIs(extractor.analyze_audio_features, analyzer.analyze_audio_features)
        self.assertIs(extractor.detect_duplicates, analyzer.detect_duplicates)
        self.assertIs(extractor.export_spotify_features_csv, analyzer.export_spotify_features_csv)

    def test_generate_sync_tags_handles_non_string_metadata_values(self):
        tags = analyzer.generate_sync_tags(
            {
                "genre": ["EDM", "Trap"],
                "mood": ["uplifting"],
                "instruments": ["guitar", "synth"],
                "bpm": "128",
            }
        )

        self.assertTrue({"energetic", "dark", "positive", "organic", "electronic", "fast"}.issubset(tags))

    def test_summarize_metadata_reports_non_mapping_json_without_crashing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            (folder / "list.json").write_text('["a", "b"]', encoding="utf-8")
            (folder / "broken.json").write_text("{", encoding="utf-8")

            summary = analyzer.summarize_metadata(folder)

        self.assertEqual(summary["json"]["list.json"]["keys"], [])
        self.assertEqual(summary["json"]["list.json"]["length"], 2)
        self.assertEqual(summary["json"]["list.json"]["type"], "list")
        self.assertIn("error", summary["json"]["broken.json"])

    def test_combine_all_metadata_skips_non_object_json_and_missing_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            (folder / "valid.json").write_text('{"title": "Song"}', encoding="utf-8")
            (folder / "invalid-structure.json").write_text('["not", "metadata"]', encoding="utf-8")
            (folder / "tracks.csv").write_text(
                "id,title\n"
                "track-1,One\n"
                ",Missing One\n"
                "track-1,Duplicate\n"
                "   ,Missing Two\n",
                encoding="utf-8",
            )

            combined_json, combined_csv = analyzer.combine_all_metadata([folder])
            duplicates = analyzer.detect_duplicates(combined_csv)

        self.assertEqual(combined_json, {"valid": {"title": "Song"}})
        self.assertEqual(len(combined_csv), 4)
        self.assertEqual(duplicates, [{"id": "track-1", "title": "Duplicate"}])

    def test_analyze_audio_features_reports_missing_file_without_exposing_full_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.wav"
            result = analyzer.analyze_audio_features(missing)

        self.assertEqual(
            result,
            {"error": "Audio analysis failed for missing.wav: audio file does not exist"},
        )
        self.assertNotIn(str(missing.parent), result["error"])

    def test_analyze_energy_danceability_handles_empty_audio(self):
        result = analyzer.analyze_energy_danceability(np.array([]), 44100)

        self.assertEqual(
            result,
            {
                "energy": 0.5,
                "danceability": 0.5,
                "acousticness": 0.5,
                "movement": 0.5,
            },
        )

    def test_export_spotify_features_csv_returns_written_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "spotify_features.csv"
            exported = analyzer.export_spotify_features_csv(
                {"Track A": {"bpm": 120, "mood": "driving"}},
                output_path=output_path,
            )

            self.assertEqual(Path(exported), output_path.resolve())
            self.assertIn("track_name", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
