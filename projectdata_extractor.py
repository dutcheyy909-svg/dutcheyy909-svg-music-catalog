"""Compatibility wrapper for the canonical project data analyzer module."""

import importlib.util
import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
ANALYZER_MODULE_NAME = "projectdata_analyzer"
ANALYZER_PATH = MODULE_DIR / f"{ANALYZER_MODULE_NAME}.py"

_analyzer = sys.modules.get(ANALYZER_MODULE_NAME)
if _analyzer is None:
    spec = importlib.util.spec_from_file_location(ANALYZER_MODULE_NAME, ANALYZER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load analyzer module from {ANALYZER_PATH}")

    _analyzer = importlib.util.module_from_spec(spec)
    sys.modules[ANALYZER_MODULE_NAME] = _analyzer
    try:
        spec.loader.exec_module(_analyzer)
    except Exception:
        sys.modules.pop(ANALYZER_MODULE_NAME, None)
        raise

csv = _analyzer.csv
defaultdict = _analyzer.defaultdict
json = _analyzer.json
librosa = _analyzer.librosa
LOGGER = _analyzer.LOGGER
np = _analyzer.np
Path = _analyzer.Path

detect_file_types = _analyzer.detect_file_types
summarize_metadata = _analyzer.summarize_metadata
generate_sync_tags = _analyzer.generate_sync_tags
analyze_valence = _analyzer.analyze_valence
analyze_instrumentalness = _analyzer.analyze_instrumentalness
analyze_liveness = _analyzer.analyze_liveness
combine_all_metadata = _analyzer.combine_all_metadata
detect_duplicates = _analyzer.detect_duplicates
analyze_energy_danceability = _analyzer.analyze_energy_danceability
analyze_audio_features = _analyzer.analyze_audio_features
infer_mood = _analyzer.infer_mood
generate_report = _analyzer.generate_report
export_songtradr_metadata = _analyzer.export_songtradr_metadata
export_audiosparx_metadata = _analyzer.export_audiosparx_metadata
export_ringo_metadata = _analyzer.export_ringo_metadata
export_spotify_features_csv = _analyzer.export_spotify_features_csv
export_spotify_csv = _analyzer.export_spotify_features_csv

__all__ = [
    "analyze_audio_features",
    "analyze_energy_danceability",
    "analyze_instrumentalness",
    "analyze_liveness",
    "analyze_valence",
    "combine_all_metadata",
    "csv",
    "defaultdict",
    "detect_duplicates",
    "detect_file_types",
    "export_audiosparx_metadata",
    "export_ringo_metadata",
    "export_songtradr_metadata",
    "export_spotify_csv",
    "export_spotify_features_csv",
    "generate_report",
    "generate_sync_tags",
    "infer_mood",
    "json",
    "librosa",
    "LOGGER",
    "np",
    "Path",
    "summarize_metadata",
]
