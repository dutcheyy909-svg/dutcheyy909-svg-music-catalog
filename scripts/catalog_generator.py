import json
from pathlib import Path

tracks = []

for file in Path(".").rglob("*.json"):
    try:
        with open(file, "r") as f:
            data = json.load(f)
            tracks.append(data)
    except:
        pass

with open("CATALOG.md", "w") as f:
    f.write("# DUTCHEYY Music Catalog\n\n")

    for track in tracks:
        f.write(f"## {track.get('title', 'Unknown')}\n")
        f.write(f"Artist: {track.get('artist', 'Unknown')}\n")
        f.write(f"Genre: {track.get('genre', 'Unknown')}\n")
        f.write(f"BPM: {track.get('bpm', 'Unknown')}\n")
        f.write(f"Mood: {track.get('mood', 'Unknown')}\n\n")

print(f"Processed {len(tracks)} tracks")
