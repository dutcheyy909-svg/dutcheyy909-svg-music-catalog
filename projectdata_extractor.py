from projectdata_analyzer import (
    detect_file_types,
    summarize_metadata,
    combine_all_metadata,
    detect_duplicates,
    generate_report,
    generate_sync_tags   # ← ADD THIS
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

        # Analyzer functions
        print("\n📌 File types:", detect_file_types(f))
        print("📌 Summary:", summarize_metadata(f))

    # Generate sync tags for each folder's metadata
    combined_json, _ = combine_all_metadata(extracted)
    for name, data in combined_json.items():
        tags = generate_sync_tags(data)
        print(f"🎵 Sync Tags for {name}: {tags}")

    # Generate final report
    report_path = generate_report(extracted)
    print(f"\n📄 Analysis report generated: {report_path}")


if __name__ == "__main__":
    run(".")

    run(".")
