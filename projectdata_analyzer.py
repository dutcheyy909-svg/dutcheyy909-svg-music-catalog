import json
import csv
from pathlib import Path
from collections import defaultdict
import librosa
import numpy as np

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
                with open(file) as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    summary["json"][file.name] = {
                        "keys": list(data.keys()),
                        "length": len(data)
                    }
                else:
                    summary["json"][file.name] = {
                        "keys": [],
                        "length": len(data) if hasattr(data, "__len__") else 0
                    }
            except Exception as e:
                summary["json"][file.name] = {"error": str(e)}

        elif file.suffix.lower() == ".csv":
            try:
                with open(file) as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                summary["csv"][file.name] = {
                    "columns": rows[0] if rows else [],
                    "rows": len(rows)
                }
            except Exception as e:
                summary["csv"][file.name] = {"error": str(e)}

    return summary


# ---------------------------------------------------------
#  Sync Licensing Tag Generator (metadata-based)
# ---------------------------------------------------------

def _safe_lower(value):
    """Safely coerce a value to a lowercase string."""
    if value is None:
        return ""
    return str(value).lower()


def generate_sync_tags(metadata, audio_features=None):
    tags = []

    if not isinstance(metadata, dict):
        metadata = {}
    if audio_features is not None and not isinstance(audio_features, dict):
        audio_features = None

    # Genre-based tags
    genre = _safe_lower(metadata.get("genre", ""))
    if "edm" in genre:
        tags += ["energetic", "modern", "sports", "gaming", "upbeat"]
    if "trap" in genre:
        tags += ["dark", "urban", "gritty", "hip-hop", "intense"]
    if "lofi" in genre:
        tags += ["chill", "study", "relaxed", "soft beats"]
    if "piano" in genre or "emotional" in genre:
        tags += ["emotional", "cinematic", "heartfelt", "film", "advertising"]

    # Mood-based tags
    mood = _safe_lower(metadata.get("mood", ""))
    if "uplifting" in mood:
        tags += ["positive", "corporate", "advertising", "feel-good"]
    if "tension" in mood:
        tags += ["suspense", "crime", "drama", "trailer"]

    # Instrument-based tags
    instruments = _safe_lower(metadata.get("instruments", ""))
    if "guitar" in instruments:
        tags += ["organic", "warm", "indie"]
    if "synth" in instruments:
        tags += ["electronic", "futuristic", "digital"]

    # BPM-based tags (metadata)
    bpm = metadata.get("bpm")
    if bpm:
        try:
            bpm = int(bpm)
            if bpm < 70:
                tags.append("slow")
            elif bpm < 110:
                tags.append("mid-tempo")
            else:
                tags.append("fast")
        except (TypeError, ValueError):
            pass

    # Audio-analysis tags
    if audio_features:
        if audio_features.get("mood"):
            tags.append(audio_features["mood"])

        af_bpm = audio_features.get("bpm")
        if af_bpm:
            try:
                af_bpm = int(af_bpm)
                if af_bpm < 70:
                    tags.append("slow")
                elif af_bpm < 110:
                    tags.append("mid-tempo")
                else:
                    tags.append("fast")
            except (TypeError, ValueError):
                pass

    return list(set(tags))


def analyze_valence(y, sr):
    """
    Rough valence estimate (happy vs sad) using key + brightness.
    """
    try:
        # Brightness
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        brightness = float(np.mean(centroid)) if centroid.size else 0.0

        # Chroma (key-ish)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        major_energy = float(np.mean(chroma[0:6])) if chroma.size else 0.0   # C–F#
        minor_energy = float(np.mean(chroma[6:12])) if chroma.size else 0.0  # G–B

        key_bias = major_energy - minor_energy

        # Combine
        valence = (brightness / 5000.0) * 0.6 + (key_bias) * 0.4
        return max(0.0, min(valence, 1.0))
    except Exception:
        return 0.5


def analyze_instrumentalness(y, sr):
    """
    Approximate instrumentalness: less vocal‑like energy → more instrumental.
    """
    try:
        # MFCCs: vocal presence often shows strong mid‑range MFCCs
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mid_band = mfcc[4:9]  # rough vocal region
        mid_energy = float(np.mean(np.abs(mid_band))) if mid_band.size else 0.0

        instrumentalness = 1.0 - (mid_energy / 200.0)
        return max(0.0, min(instrumentalness, 1.0))
    except Exception:
        return 0.5


def analyze_liveness(y, sr):
    """
    Approximate liveness: more transient, noisy, room‑like → higher liveness.
    """
    try:
        # Onset density
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_density = float(np.mean(onset_env)) if onset_env.size else 0.0

        # High‑frequency energy
        spec = librosa.stft(y)
        freqs = librosa.fft_frequencies(sr=sr)
        high_band = spec[freqs > 6000]
        high_energy = float(np.mean(np.abs(high_band))) if high_band.size > 0 else 0.0

        liveness = (onset_density / 5.0) * 0.6 + (high_energy / 5.0) * 0.4
        return max(0.0, min(liveness, 1.0))
    except Exception:
        return 0.5


# ---------------------------------------------------------
#  Combine all JSON + CSV into unified structures
# ---------------------------------------------------------

def combine_all_metadata(extracted_folders):
    combined_json = {}
    combined_csv = []

    for folder in extracted_folders:
        folder = Path(folder)

        # JSON merge
        for file in folder.glob("*.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                combined_json[file.stem] = data
            except Exception:
                pass

        # CSV merge
        for file in folder.glob("*.csv"):
            try:
                with open(file) as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                if rows:
                    header = rows[0]
                    for row in rows[1:]:
                        combined_csv.append(dict(zip(header, row)))
            except Exception:
                pass

    return combined_json, combined_csv


# ---------------------------------------------------------
#  Detect duplicates across all extracted metadata
# ---------------------------------------------------------

def detect_duplicates(combined_csv, key="id"):
    seen = set()
    duplicates = []

    for row in combined_csv:
        value = row.get(key)
        if value in seen:
            duplicates.append(row)
        else:
            seen.add(value)

    return duplicates


# ---------------------------------------------------------
#  Audio Analysis (BPM, brightness, mood)
# ---------------------------------------------------------

def _get_tempo(y, sr):
    """Get tempo, supporting both old (librosa.beat.tempo) and new
    (librosa.feature.tempo) librosa APIs."""
    try:
        tempos = librosa.feature.tempo(y=y, sr=sr)
    except AttributeError:
        tempos = librosa.beat.tempo(y=y, sr=sr)
    return float(tempos[0]) if getattr(tempos, "size", 0) else 0.0


def analyze_energy_danceability(y, sr):
    """Infer normalized energy, danceability, acousticness, and movement."""
    try:
        rms = librosa.feature.rms(y=y)
        mean_rms = float(np.mean(rms)) if rms.size else 0.0
        energy = max(0.0, min(1.0, mean_rms / 0.1))

        tempo = _get_tempo(y, sr)

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_density = float(np.mean(onset_env)) if onset_env.size else 0.0
        tempo_norm = min(1.0, tempo / 150.0)
        onset_norm = min(1.0, onset_density / 5.0)
        danceability = max(0.0, min(1.0, tempo_norm * 0.6 + onset_norm * 0.4))

        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        rolloff_mean = float(np.mean(rolloff)) if rolloff.size else 0.0
        acousticness = 1.0 - min(1.0, rolloff_mean / (sr / 2.0)) if sr else 0.5

        spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        movement = float(np.mean(spec_bw)) if spec_bw.size else 0.0
        movement = max(0.0, min(1.0, movement / 5000.0))

        return {
            "energy": energy,
            "danceability": danceability,
            "acousticness": max(0.0, min(1.0, acousticness)),
            "movement": movement
        }
    except Exception:
        return {
            "energy": 0.5,
            "danceability": 0.5,
            "acousticness": 0.5,
            "movement": 0.5
        }


def analyze_audio_features(audio_path):
    try:
        y, sr = librosa.load(audio_path, sr=None)

        # BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = int(tempo)

        # Brightness
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        brightness = float(np.mean(centroid)) if centroid.size else 0.0

        # Mood
        mood = infer_mood(bpm, brightness)

        # Energy + danceability
        extra = analyze_energy_danceability(y, sr)

        # Spotify‑style extras
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
            "liveness": liveness
        }

    except Exception as e:
        return {"error": str(e)}


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
#  Generate a simple text report
# ---------------------------------------------------------

def generate_report(extracted_folders, output="ProjectData_Report.txt"):
    combined_json, combined_csv = combine_all_metadata(extracted_folders)
    duplicates = detect_duplicates(combined_csv)

    with open(output, "w") as f:
        f.write("=== ProjectData Analysis Report ===\n\n")
        f.write(f"Folders analyzed: {len(extracted_folders)}\n\n")

        f.write("JSON Files Combined:\n")
        for name in combined_json:
            f.write(f" - {name}\n")

        f.write("\nCSV Rows Combined: " + str(len(combined_csv)) + "\n")
        f.write("Duplicate Entries: " + str(len(duplicates)) + "\n")

        f.write("\nSync Licensing Tags:\n")
        for name, data in combined_json.items():
            if not isinstance(data, dict):
                f.write(f" - {name}: (skipped, not an object)\n")
                continue
            tags = generate_sync_tags(data)
            f.write(f" - {name}: {', '.join(tags)}\n")


def export_songtradr_metadata(track_name, metadata, audio_features=None):
    """Return Songtradr-ready metadata dict."""
    metadata = metadata or {}
    audio_features = audio_features or {}
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
        "pro": metadata.get("pro_affiliation", "")
    }


def export_audiosparx_metadata(track_name, metadata, audio_features=None):
    """Return AudioSparx-ready metadata dict."""
    metadata = metadata or {}
    audio_features = audio_features or {}
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
        "VersionsAvailable": metadata.get("versions_available", [])
    }


def export_ringo_metadata(track_name, metadata, audio_features=None):
    """Return Ringo-ready metadata dict."""
    metadata = metadata or {}
    audio_features = audio_features or {}
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
        "publisher": metadata.get("publisher", "")
    }
