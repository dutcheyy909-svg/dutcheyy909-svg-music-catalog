from projectdata_analyzer import (
    detect_file_types,
    summarize_metadata,
    combine_all_metadata,
    detect_duplicates,
    generate_report,
    generate_sync_tags,
    analyze_audio_features,
    export_songtradr_metadata,
    export_audiosparx_metadata,
    export_ringo_metadata
)

import zipfile
import json
import csv
from pathlib import Path

def extract_zip(zip_path: Path, extract_to: Path):
    """Extract a single ZIP file into a target folder."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"📦 Extracted: {zip_path.name} → {extract_to}")
        return True
    except zipfile.BadZipFile:
        print(f"⚠️ Bad ZIP file: {zip_path.name}")
        return False


def inspect_extracted_folder(folder: Path):
    """Inspect JSON and CSV files inside an extracted ProjectData folder."""
    print(f"\n🔍 Inspecting: {folder}")

    for file in folder.glob("*.json"):
        try:
            with open(file, "r") as f:
                data = json.load(f)
            print(f"🟢 JSON: {file.name} → keys: {list(data.keys())}")
        except Exception as e:
            print(f"⚠️ Could not read JSON {file.name}: {e}")

    for file in folder.glob("*.csv"):
        try:
            with open(file, newline="") as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
            print(f"🟡 CSV: {file.name} → first row: {first_row}")
        except Exception as e:
            print(f"⚠️ Could not read CSV {file.name}: {e}")


def extract_all_projectdata(folder="."):
    """Find and extract all ProjectData ZIP files."""
    folder = Path(folder)
    zip_files = sorted(folder.glob("ProjectData*.zip"))

    if not zip_files:
        print("⚠️ No ProjectData ZIP files found.")
        return []

    extracted_folders = []

    for zip_file in zip_files:
        extract_to = folder / zip_file.stem
        extract_to.mkdir(exist_ok=True)

        if extract_zip(zip_file, extract_to):
            extracted_folders.append(extract_to)

    return extracted_folders


def run(folder="."):
    """Main workflow: extract, inspect, analyze, and generate report."""
    extracted = extract_all_projectdata(folder)

    for f in extracted:
        inspect_extracted_folder(f)

        print("\n📌 File types:", detect_file_types(f))
        print("📌 Summary:", summarize_metadata(f))

    combined_json, _ = combine_all_metadata(extracted)

    # Audio analysis + sync tags + library metadata
    for f in extracted:
        audio_files = list(f.glob("*.wav")) + list(f.glob("*.mp3"))

        for audio in audio_files:
            print(f"\n🎧 Analyzing audio: {audio.name}")
            audio_features = analyze_audio_features(audio)

            print(f"   BPM: {audio_features.get('bpm')}")
            print(f"   Brightness: {audio_features.get('brightness')}")
            print(f"   Mood: {audio_features.get('mood')}")

            track_name = audio.stem
            metadata = combined_json.get(track_name, {})

            tags = generate_sync_tags(metadata, audio_features)
            print(f"   🎵 Sync Tags: {tags}")

            # Export formats
            songtradr_meta = export_songtradr_metadata(track_name, metadata, audio_features)
            audiosparx_meta = export_audiosparx_metadata(track_name, metadata, audio_features)
            ringo_meta = export_ringo_metadata(track_name, metadata, audio_features)

            print("\n🎼 Songtradr:", songtradr_meta)
            print("🎧 AudioSparx:", audiosparx_meta)
            print("🎬 Ringo:", ringo_meta)

    report_path = generate_report(extracted)
    print(f"\n📄 Analysis report generated: {report_path}") 
    if __name__ == "__main__":
    run(".")


