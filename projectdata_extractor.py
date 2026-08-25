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

    # Defensive casting in case fields are not strings
    genre = str(metadata.get("genre", "")).lower()
    if "edm" in genre:
        tags += ["energetic", "modern", "sports", "gaming", "upbeat"]
    if "trap" in genre:
        tags += ["dark", "urban", "gritty", "hip-hop", "intense"]
    if "lofi" in genre:
        tags += ["chill", "study", "relaxed", "soft beats"]
    if "piano" in genre or "emotional" in genre:
        tags += ["emotional", "cinematic", "heartfelt", "film", "advertising"]

    # Mood-based tags
    mood = str(metadata.get("mood", "")).lower()
    if "uplifting" in mood:
        tags += ["positive", "corporate", "advertising", "feel-good"]
    if "tension" in mood:
        tags += ["suspense", "crime", "drama", "trailer"]

    # Instrument-based tags
    instruments = str(metadata.get("instruments", "")).lower()
    if "guitar" in instruments:
        tags += ["organic", "warm", "indie"]
    if "synth" in instruments:
        tags += ["electronic", "futuristic", "digital"]

    # BPM-based tags (metadata)
    bpm_meta = metadata.get("bpm")
    if bpm_meta:
        try:
            bpm_val = int(bpm_meta)
            if bpm_val < 70:
                tags.append("slow")
            elif bpm_val < 110:
                tags.append("mid-tempo")
            else:
                tags.append("fast")
        except Exception:
            pass

    # Audio-analysis tags
    if audio_features:
        if audio_features.get("mood"):
            tags.append(audio_features["mood"])

        if audio_features.get("bpm"):
            try:
                bpm_af = int(audio_features["bpm"])
                if bpm_af < 70:
                    tags.append("slow")
                elif bpm_af < 110:
                    tags.append("mid-tempo")
                else:
                    tags.append("fast")
            except Exception:
                pass

    return list(set(tags))


# ---------------------------------------------------------
#  Additional audio analysis helpers (valence, instrumentalness, liveness)
# ---------------------------------------------------------

def analyze_valence(y, sr):
    """
    Rough valence estimate (happy vs sad) using brightness + chroma balance.
    Returns a float in [0.0, 1.0].
    """
    try:
        # Brightness (spectral centroid)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        brightness = float(np.mean(centroid)) if centroid.size else 0.0

        # Chroma energy: average energy per pitch class, then compare first half vs second half
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        if chroma.size:
            # mean energy per pitch class, then average first 6 vs last 6
            major_energy = float(np.mean(chroma[0:6]))
            minor_energy = float(np.mean(chroma[6:12]))
        else:
            major_energy = 0.0
            minor_energy = 0.0

        key_bias = major_energy - minor_energy

        # Normalize brightness to rough 0-1 by dividing by an expected range
        brightness_norm = brightness / 5000.0
        valence_raw = (brightness_norm * 0.6) + (key_bias * 0.4)
        valence = max(0.0, min(1.0, valence_raw))
        return valence
    except Exception:
        return 0.5


def analyze_instrumentalness(y, sr):
    """
    Approximate instrumentalness: less vocal-like mid-band energy → more instrumental.
    Returns float in [0.0, 1.0].
    """
    try:
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        if mfcc.size:
            mid_band = mfcc[4:9]
            mid_energy = float(np.mean(np.abs(mid_band)))
        else:
            mid_energy = 0.0

        # Empirical scaling: mid_energy typically in range 0-100; clamp and invert.
        instrumentalness = 1.0 - (mid_energy / 200.0)
        return max(0.0, min(1.0, instrumentalness))
    except Exception:
        return 0.5


def analyze_liveness(y, sr):
    """
    Approximate liveness: more transient / high-frequency energy → higher liveness.
    Returns float in [0.0, 1.0].
    """
    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_density = float(np.mean(onset_env)) if onset_env.size else 0.0

        # STFT and frequency axis
        n_fft = 2048
        S = np.abs(librosa.stft(y, n_fft=n_fft))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
        # select bins > 6000 Hz
        high_idx = np.where(freqs > 6000)[0]
        if high_idx.size > 0:
            high_band = S[high_idx, :]
            high_energy = float(np.mean(high_band))
        else:
            high_energy = 0.0

        # Normalize empirically and combine
        liveness_raw = (onset_density / 5.0) * 0.6 + (high_energy / 5.0) * 0.4
        liveness = max(0.0, min(1.0, liveness_raw))
        return liveness
    except Exception:
        return 0.0


# ---------------------------------------------------------
#  Estimate energy/danceability/acousticness/movement
# ---------------------------------------------------------

def analyze_energy_danceability(y, sr):
    """
    Return a dict with rough estimates for:
      - energy: 0.0..1.0 (RMS-based)
      - danceability: 0.0..1.0 (tempo + onset density heuristic)
      - acousticness: 0.0..1.0 (inverted spectral rolloff)
      - movement: 0.0..1.0 (spectral bandwidth)
    These are heuristics — not a replacement for Spotify features — but useful for tagging.
    """
    try:
        # RMS energy
        rms = librosa.feature.rms(y=y)
        mean_rms = float(np.mean(rms)) if rms.size else 0.0
        energy = max(0.0, min(1.0, mean_rms / 0.1))  # scale: typical rms values < 0.1

        # Tempo (beats per minute)
        tempos = librosa.beat.tempo(y=y, sr=sr)
        tempo = float(tempos[0]) if tempos.size else 0.0

        # Onset strength
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_density = float(np.mean(onset_env)) if onset_env.size else 0.0

        # Danceability heuristic: tempo and rhythmic onset density
        # tempo normalized roughly 0-150 -> 0..1, onset_density normalized by ~5
        tempo_norm = min(1.0, tempo / 150.0)
        onset_norm = min(1.0, onset_density / 5.0)
        danceability = max(0.0, min(1.0, tempo_norm * 0.6 + onset_norm * 0.4))

        # Acousticness: use spectral rolloff (lower rolloff -> more acoustic)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        rolloff_mean = float(np.mean(rolloff)) if rolloff.size else 0.0
        # rolloff is in Hz: invert and normalize with sr/2
        acousticness = 1.0 - min(1.0, rolloff_mean / (sr / 2.0))

        # Movement: spectral bandwidth normalized
        spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        movement = float(np.mean(spec_bw)) if spec_bw.size else 0.0
        movement = max(0.0, min(1.0, movement / 5000.0))

        return {
            "energy": energy,
            "danceability": danceability,
            "acousticness": acousticness,
            "movement": movement
        }
    except Exception:
        return {
            "energy": 0.5,
            "danceability": 0.5,
            "acousticness": 0.5,
            "movement": 0.5
        }


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
            except Exception as e:
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
            except Exception as e:
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
#  Audio Analysis (BPM, brightness, mood, extras)
# ---------------------------------------------------------

def analyze_audio_features(audio_path):
    try:
        y, sr = librosa.load(audio_path, sr=None)

        # BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = int(tempo) if tempo is not None else 0

        # Brightness
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        brightness = float(np.mean(centroid)) if centroid.size else 0.0

        # Mood
        mood = infer_mood(bpm, brightness)

        # Energy + danceability + acousticness + movement
        extra = analyze_energy_danceability(y, sr)

        # Spotify‑style extras
        valence = analyze_valence(y, sr)
        instrumentalness = analyze_instrumentalness(y, sr)
        liveness = analyze_liveness(y, sr)

        return {
            "bpm": bpm,
            "brightness": brightness,
            "mood": mood,
            "energy": extra.get("energy"),
            "danceability": extra.get("danceability"),
            "acousticness": extra.get("acousticness"),
            "movement": extra.get("movement"),
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
#  Export Spotify-style CSV
# ---------------------------------------------------------

def export_spotify_features_csv(spotify_export, output_path="spotify_features.csv"):
    """
    Export audio features to CSV in Spotify-style format.
    
    Args:
        spotify_export (dict): Dictionary with track names as keys and feature dicts as values.
        output_path (str): Path to output CSV file.
    
    Returns:
        str: Path to the exported CSV file.
    """
    try:
        if not spotify_export:
            return None
        
        # Get all unique keys from all feature dictionaries
        fieldnames = set(["track_name"])
        for features in spotify_export.values():
            if isinstance(features, dict):
                fieldnames.update(features.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        # Write CSV
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for track_name, features in spotify_export.items():
                row = {"track_name": track_name}
                if isinstance(features, dict):
                    row.update(features)
                writer.writerow(row)
        
        return str(Path(output_path).resolve())
    
    except Exception as e:
        print(f"Error exporting Spotify features CSV: {e}")
        return None


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


# ---------------------------------------------------------
#  Main Execution (example usage)
# ---------------------------------------------------------

if __name__ == "__main__":
    # Example: Extract and export Spotify features
    # extracted = [Path("./ProjectData_1"), Path("./ProjectData_2")]  # Define extracted folders
    # 
    # spotify_export = {}
    # for f in extracted:
    #     audio_files = list(f.glob("*.wav")) + list(f.glob("*.mp3"))
    #     for audio in audio_files:
    #         track_name = audio.stem
    #         audio_features = analyze_audio_features(audio)
    #         spotify_export[track_name] = audio_features
    # 
    # csv_path = export_spotify_features_csv(spotify_export)
    # print(f"📄 Exported Spotify-style CSV: {csv_path}")
    pass
