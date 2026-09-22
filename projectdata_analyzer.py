import csv
import json
import logging
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

import librosa
import numpy as np

LOGGER = logging.getLogger(__name__)

__all__ = [
    "analyze_audio_features",
    "analyze_energy_danceability",
    "analyze_instrumentalness",
    "analyze_liveness",
    "analyze_valence",
    "combine_all_metadata",
    "detect_duplicates",
    "detect_file_types",
    "export_audiosparx_metadata",
    "export_ringo_metadata",
    "export_songtradr_metadata",
    "export_spotify_features_csv",
    "generate_report",
    "generate_sync_tags",
    "infer_mood",
    "summarize_metadata",
]


def _coerce_mapping(value):
    return value if isinstance(value, Mapping) else {}


def _metadata_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, (list, tuple, set)):
        return " ".join(str(item) for item in value).lower()
    return str(value).lower()


def _coerce_bpm(value):
    if value in (None, ""):
        return None
    return int(float(value))


def _safe_length(value):
    try:
        return len(value)
    except TypeError:
        return None


def _normalize_duplicate_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


def _validate_audio_inputs(y, sr):
    if y is None:
        raise ValueError("audio signal is missing")

    audio = np.asarray(y)
    if audio.size == 0:
        raise ValueError("audio signal is empty")
    if not np.issubdtype(audio.dtype, np.number):
        raise ValueError("audio signal must be numeric")
    if not isinstance(sr, (int, float, np.integer, np.floating)) or sr <= 0:
        raise ValueError("sample rate must be positive")

    return audio, sr


# ---------------------------------------------------------
#  Detect file types inside extracted ProjectData folders
# ---------------------------------------------------------

def detect_file_types(folder):
    folder = Path(folder)
    types = defaultdict(list)

    for file in folder.iterdir():
        if file.is_file():
            types[file.suffix.lower()].append(file.name)

    return dict(types)


# ---------------------------------------------------------
#  Summarise metadata from JSON + CSV files
# ---------------------------------------------------------

def summarize_metadata(folder):
    folder = Path(folder)
    summary = {"json": {}, "csv": {}}

    for file in folder.glob("*"):
        if file.suffix.lower() == ".json":
            try:
                with file.open(encoding="utf-8") as handle:
                    data = json.load(handle)
                keys = list(data.keys()) if isinstance(data, dict) else []
                summary["json"][file.name] = {
                    "keys": keys,
                    "length": _safe_length(data),
                    "type": type(data).__name__,
                }
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                summary["json"][file.name] = {"error": str(exc)}

        elif file.suffix.lower() == ".csv":
            try:
                with file.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.reader(handle))
                summary["csv"][file.name] = {
                    "columns": rows[0] if rows else [],
                    "rows": len(rows),
                }
            except (OSError, UnicodeDecodeError, csv.Error, TypeError, ValueError) as exc:
                summary["csv"][file.name] = {"error": str(exc)}

    return summary


# ---------------------------------------------------------
#  Sync Licensing Tag Generator (metadata-based)
# ---------------------------------------------------------

def generate_sync_tags(metadata, audio_features=None):
    metadata = _coerce_mapping(metadata)
    audio_features = _coerce_mapping(audio_features)
    tags = []

    genre = _metadata_text(metadata.get("genre"))
    if "edm" in genre:
        tags += ["energetic", "modern", "sports", "gaming", "upbeat"]
    if "trap" in genre:
        tags += ["dark", "urban", "gritty", "hip-hop", "intense"]
    if "lofi" in genre:
        tags += ["chill", "study", "relaxed", "soft beats"]
    if "piano" in genre or "emotional" in genre:
        tags += ["emotional", "cinematic", "heartfelt", "film", "advertising"]

    mood = _metadata_text(metadata.get("mood"))
    if "uplifting" in mood:
        tags += ["positive", "corporate", "advertising", "feel-good"]
    if "tension" in mood:
        tags += ["suspense", "crime", "drama", "trailer"]

    instruments = _metadata_text(metadata.get("instruments"))
    if "guitar" in instruments:
        tags += ["organic", "warm", "indie"]
    if "synth" in instruments:
        tags += ["electronic", "futuristic", "digital"]

    try:
        bpm_meta = _coerce_bpm(metadata.get("bpm"))
    except (TypeError, ValueError):
        bpm_meta = None

    if bpm_meta is not None:
        if bpm_meta < 70:
            tags.append("slow")
        elif bpm_meta < 110:
            tags.append("mid-tempo")
        else:
            tags.append("fast")

    if audio_features.get("mood"):
        tags.append(str(audio_features["mood"]))

    try:
        bpm_audio = _coerce_bpm(audio_features.get("bpm"))
    except (TypeError, ValueError):
        bpm_audio = None

    if bpm_audio is not None:
        if bpm_audio < 70:
            tags.append("slow")
        elif bpm_audio < 110:
            tags.append("mid-tempo")
        else:
            tags.append("fast")

    return list(dict.fromkeys(tags))


def analyze_valence(y, sr):
    """
    Rough valence estimate (happy vs sad) using key + brightness.
    """
    try:
        y, sr = _validate_audio_inputs(y, sr)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        brightness = float(np.mean(centroid)) if centroid.size else 0.0

        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        major_energy = float(np.mean(chroma[0:6])) if chroma.size else 0.0
        minor_energy = float(np.mean(chroma[6:12])) if chroma.size else 0.0

        key_bias = major_energy - minor_energy
        valence = (brightness / 5000.0) * 0.6 + key_bias * 0.4
        return max(0.0, min(valence, 1.0))
    except Exception as exc:
        LOGGER.warning("Unable to estimate valence: %s", exc)
        return 0.5


def analyze_instrumentalness(y, sr):
    """
    Approximate instrumentalness: less vocal‑like energy → more instrumental.
    """
    try:
        y, sr = _validate_audio_inputs(y, sr)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mid_band = mfcc[4:9]
        mid_energy = float(np.mean(np.abs(mid_band))) if mid_band.size else 0.0

        instrumentalness = 1.0 - (mid_energy / 200.0)
        return max(0.0, min(instrumentalness, 1.0))
    except Exception as exc:
        LOGGER.warning("Unable to estimate instrumentalness: %s", exc)
        return 0.5


def analyze_liveness(y, sr):
    """
    Approximate liveness: more transient, noisy, room‑like → higher liveness.
    """
    try:
        y, sr = _validate_audio_inputs(y, sr)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_density = float(np.mean(onset_env)) if onset_env.size else 0.0

        spec = librosa.stft(y)
        freqs = librosa.fft_frequencies(sr=sr)
        high_band = spec[freqs > 6000]
        high_energy = float(np.mean(np.abs(high_band))) if high_band.size > 0 else 0.0

        liveness = (onset_density / 5.0) * 0.6 + (high_energy / 5.0) * 0.4
        return max(0.0, min(liveness, 1.0))
    except Exception as exc:
        LOGGER.warning("Unable to estimate liveness: %s", exc)
        return 0.0


# ---------------------------------------------------------
#  Combine all JSON + CSV into unified structures
# ---------------------------------------------------------

def combine_all_metadata(extracted_folders):
    combined_json = {}
    combined_csv = []

    for folder in extracted_folders:
        folder = Path(folder)

        for file in folder.glob("*.json"):
            try:
                with file.open(encoding="utf-8") as handle:
                    data = json.load(handle)
                if not isinstance(data, dict):
                    LOGGER.warning("Skipping JSON metadata in %s because the top-level value is %s", file.name, type(data).__name__)
                    continue
                combined_json[file.stem] = data
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                LOGGER.warning("Skipping unreadable JSON metadata in %s: %s", file.name, exc)

        for file in folder.glob("*.csv"):
            try:
                with file.open(encoding="utf-8", newline="") as handle:
                    reader = csv.DictReader(handle)
                    if not reader.fieldnames:
                        continue

                    for row_number, row in enumerate(reader, start=2):
                        cleaned_row = dict(row)
                        if None in cleaned_row:
                            LOGGER.warning("Ignoring extra CSV columns in %s row %s", file.name, row_number)
                            cleaned_row.pop(None, None)
                        combined_csv.append(cleaned_row)
            except (OSError, UnicodeDecodeError, csv.Error, TypeError, ValueError) as exc:
                LOGGER.warning("Skipping unreadable CSV metadata in %s: %s", file.name, exc)

    return combined_json, combined_csv


# ---------------------------------------------------------
#  Detect duplicates across all extracted metadata
# ---------------------------------------------------------

def detect_duplicates(combined_csv, key="id"):
    seen = set()
    duplicates = []

    for row in combined_csv:
        if not isinstance(row, Mapping):
            LOGGER.warning("Skipping duplicate detection for non-mapping row")
            continue

        value = _normalize_duplicate_value(row.get(key))
        if value is None:
            continue
        try:
            hash(value)
        except TypeError:
            LOGGER.warning("Skipping duplicate detection for unhashable %s value", key)
            continue

        if value in seen:
            duplicates.append(row)
        else:
            seen.add(value)

    return duplicates


# ---------------------------------------------------------
#  Audio Analysis (BPM, brightness, mood)
# ---------------------------------------------------------
def analyze_energy_danceability(y, sr):
    """Infer normalized energy, danceability, acousticness, and movement."""
    try:
        y, sr = _validate_audio_inputs(y, sr)
        rms = librosa.feature.rms(y=y)
        mean_rms = float(np.mean(rms)) if rms.size else 0.0
        energy = max(0.0, min(1.0, mean_rms / 0.1))

        tempos = librosa.beat.tempo(y=y, sr=sr)
        tempo = float(tempos[0]) if np.size(tempos) else 0.0

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_density = float(np.mean(onset_env)) if onset_env.size else 0.0
        tempo_norm = min(1.0, tempo / 150.0)
        onset_norm = min(1.0, onset_density / 5.0)
        danceability = max(0.0, min(1.0, tempo_norm * 0.6 + onset_norm * 0.4))

        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        rolloff_mean = float(np.mean(rolloff)) if rolloff.size else 0.0
        acousticness = 1.0 - min(1.0, rolloff_mean / (sr / 2.0))

        spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        movement = float(np.mean(spec_bw)) if spec_bw.size else 0.0
        movement = max(0.0, min(1.0, movement / 5000.0))

        return {
            "energy": energy,
            "danceability": danceability,
            "acousticness": acousticness,
            "movement": movement,
        }
    except Exception as exc:
        LOGGER.warning("Unable to estimate energy and danceability: %s", exc)
        return {
            "energy": 0.5,
            "danceability": 0.5,
            "acousticness": 0.5,
            "movement": 0.5,
        }


def analyze_audio_features(audio_path):
    audio_path = Path(audio_path)

    try:
        if not audio_path.is_file():
            raise FileNotFoundError("audio file does not exist")

        y, sr = librosa.load(audio_path, sr=None)
        y, sr = _validate_audio_inputs(y, sr)

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = int(float(tempo)) if np.size(tempo) else 0

        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        brightness = float(np.mean(centroid)) if centroid.size else 0.0
        mood = infer_mood(bpm, brightness)
        extra = analyze_energy_danceability(y, sr)

        valence = analyze_valence(y, sr)
        instrumentalness = analyze_instrumentalness(y, sr)
        liveness = analyze_liveness(y, sr)

        return {
            "bpm": bpm,
            "brightness": brightness,
            "mood": mood,
            "energy": extra["energy"],
            "danceability": extra["danceability"],
            "acousticness": extra["acousticness"],
            "movement": extra["movement"],
            "valence": valence,
            "instrumentalness": instrumentalness,
            "liveness": liveness,
        }

    except Exception as exc:
        LOGGER.warning("Unable to analyze audio features for %s: %s", audio_path.name, exc)
        return {"error": f"Audio analysis failed for {audio_path.name}: {exc}"}


def infer_mood(bpm, brightness):
    if bpm > 120 and brightness > 3000:
        return "energetic"
    if bpm > 120 and brightness < 3000:
        return "uplifting"
    if bpm < 80 and brightness < 2500:
        return "calm"
    if bpm < 80 and brightness > 2500:
        return "dark"
    if 80 <= bpm <= 120 and brightness < 2500:
        return "warm"
    if 80 <= bpm <= 120 and brightness > 2500:
        return "driving"
    return "neutral"


# ---------------------------------------------------------
#  Export Spotify-style CSV
# ---------------------------------------------------------

def export_spotify_features_csv(spotify_export, output_path="spotify_features.csv"):
    """Export audio features to CSV in Spotify-style format."""
    try:
        if not spotify_export:
            return None

        fieldnames = {"track_name"}
        for features in spotify_export.values():
            if isinstance(features, dict):
                fieldnames.update(str(key) for key in features)

        ordered_fieldnames = sorted(fieldnames)

        with open(output_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=ordered_fieldnames)
            writer.writeheader()

            for track_name, features in spotify_export.items():
                row = {"track_name": track_name}
                if isinstance(features, dict):
                    row.update({str(key): value for key, value in features.items()})
                writer.writerow(row)

        return str(Path(output_path).resolve())
    except (OSError, ValueError, TypeError, csv.Error) as exc:
        LOGGER.warning("Unable to export Spotify-style features CSV: %s", exc)
        return None


# ---------------------------------------------------------
#  Generate a simple text report
# ---------------------------------------------------------

def generate_report(extracted_folders, output="ProjectData_Report.txt"):
    combined_json, combined_csv = combine_all_metadata(extracted_folders)
    duplicates = detect_duplicates(combined_csv)

    with open(output, "w", encoding="utf-8") as handle:
        handle.write("=== ProjectData Analysis Report ===\n\n")
        handle.write(f"Folders analyzed: {len(extracted_folders)}\n\n")

        handle.write("JSON Files Combined:\n")
        for name in combined_json:
            handle.write(f" - {name}\n")

        handle.write("\nCSV Rows Combined: " + str(len(combined_csv)) + "\n")
        handle.write("Duplicate Entries: " + str(len(duplicates)) + "\n")

        handle.write("\nSync Licensing Tags:\n")
        for name, data in combined_json.items():
            tags = generate_sync_tags(data)
            handle.write(f" - {name}: {', '.join(tags)}\n")


def export_songtradr_metadata(track_name, metadata, audio_features=None):
    """Return Songtradr-ready metadata dict."""
    metadata = _coerce_mapping(metadata)
    audio_features = _coerce_mapping(audio_features)
    tags = generate_sync_tags(metadata, audio_features)

    return {
        "title": metadata.get("title", track_name),
        "description": metadata.get("description", ""),
        "bpm": audio_features.get("bpm") if audio_features else metadata.get("bpm"),
        "key": metadata.get("key", ""),
        "mood": audio_features.get("mood") if audio_features else metadata.get("mood", ""),
        "genre": metadata.get("genre", ""),
        "subgenre": metadata.get("subgenre", ""),
        "tags": tags,
        "instruments": metadata.get("instruments", ""),
        "rights": metadata.get("usage_rights", "100% owned"),
        "composer": metadata.get("composer", ""),
        "publisher": metadata.get("publisher", ""),
        "pro": metadata.get("pro_affiliation", ""),
    }


def export_audiosparx_metadata(track_name, metadata, audio_features=None):
    """Return AudioSparx-ready metadata dict."""
    metadata = _coerce_mapping(metadata)
    audio_features = _coerce_mapping(audio_features)
    tags = generate_sync_tags(metadata, audio_features)

    return {
        "TrackTitle": metadata.get("title", track_name),
        "Description": metadata.get("description", ""),
        "Genre": metadata.get("genre", ""),
        "SubGenre": metadata.get("subgenre", ""),
        "Tempo": audio_features.get("bpm") if audio_features else metadata.get("bpm"),
        "Mood": audio_features.get("mood") if audio_features else metadata.get("mood", ""),
        "Keywords": ", ".join(tags),
        "Instruments": metadata.get("instruments", ""),
        "Composer": metadata.get("composer", ""),
        "Publisher": metadata.get("publisher", ""),
        "PRO": metadata.get("pro_affiliation", ""),
        "StemsAvailable": metadata.get("stems_available", True),
        "VersionsAvailable": metadata.get("versions_available", []),
    }


def export_ringo_metadata(track_name, metadata, audio_features=None):
    """Return Ringo-ready metadata dict."""
    metadata = _coerce_mapping(metadata)
    audio_features = _coerce_mapping(audio_features)
    tags = generate_sync_tags(metadata, audio_features)

    return {
        "name": metadata.get("title", track_name),
        "bpm": audio_features.get("bpm") if audio_features else metadata.get("bpm"),
        "key": metadata.get("key", ""),
        "energy": metadata.get("energy_level", ""),
        "mood": audio_features.get("mood") if audio_features else metadata.get("mood", ""),
        "genre": metadata.get("genre", ""),
        "tags": tags,
        "recommended_scenes": metadata.get("recommended_scenes", []),
        "rights": metadata.get("usage_rights", "100% owned"),
        "composer": metadata.get("composer", ""),
        "publisher": metadata.get("publisher", ""),
    }
