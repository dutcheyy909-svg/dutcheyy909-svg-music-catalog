import json
import csv
from pathlib import Path
from collections import defaultdict

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

    return output
