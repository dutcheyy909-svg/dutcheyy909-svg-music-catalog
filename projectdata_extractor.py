"""Compatibility wrapper for the canonical project data analyzer module."""

import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
module_dir_str = str(MODULE_DIR)
added_module_dir = False
if module_dir_str not in sys.path:
    sys.path.insert(0, module_dir_str)
    added_module_dir = True

try:
    import projectdata_analyzer as _analyzer
finally:
    if added_module_dir:
        sys.path.remove(module_dir_str)

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
