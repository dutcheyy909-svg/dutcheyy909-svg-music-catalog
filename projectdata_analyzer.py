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
                summary["json"][file.name] = {
                    "keys": list(data.keys()),
                    "length": len(data)
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

def generate_sync_tags(metadata, audio_features=None):
    tags = []

    # Genre-based tags
    genre = metadata.get("genre", "").lower()
    if "edm" in genre:
        tags += ["energetic", "modern", "sports", "gaming", "upbeat"]
    if "trap" in genre:
        tags += ["dark", "urban", "gritty", "hip-hop", "intense"]
    if "lofi" in genre:
        tags += ["chill", "study", "relaxed", "soft beats"]
    if "piano" in genre or "emotional" in genre:
        tags += ["emotional", "cinematic", "heartfelt", "film", "advertising"]

    # Mood-based tags
    mood = metadata.get("mood", "").lower()
    if "uplifting" in mood:
        tags += ["positive", "corporate", "advertising", "feel-good"]
    if "tension" in mood:
        tags += ["suspense", "crime", "drama", "trailer"]

    # Instrument-based tags
    instruments = metadata.get("instruments", "").lower()
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
        except:
            pass

    # Audio-analysis tags
    if audio_features:
        if audio_features.get("mood"):
            tags.append(audio_features["mood"])

        if audio_features.get("bpm"):
            bpm = audio_features["bpm"]
            if bpm < 70:
                tags.append("slow")
            elif bpm < 110:
                tags.append("mid-tempo")
            else:
                tags.append("fast")

    return list(set(tags))


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
            except:
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
            except:
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

def analyze_audio_features(audio_path):
    try:
        y, sr = librosa.load(audio_path, sr=None)

        # BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = int(tempo)

        # Brightness (spectral centroid)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        brightness = float(np.mean(centroid))

        # Mood inference
        mood = infer_mood(bpm, brightness)

        return {
            "bpm": bpm,
            "brightness": brightness,
            "mood": mood
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
            tags = generate_sync_tags(data)
            f.write(f" - {name}: {', '.join(tags)}\n")
def export_songtradr_metadata(track_name, metadata, audio_features=None):
    """Return Songtradr-ready metadata dict."""
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

    return output
