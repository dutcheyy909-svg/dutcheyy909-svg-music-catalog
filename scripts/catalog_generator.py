import os

print("Music Catalog Generator")

for root, dirs, files in os.walk("."):
    for file in files:
        print(os.path.join(root, file))

from pathlib import Path

catalog = []

for file in Path(".").rglob("*.json"):
    catalog.app*nd(str(file))

with open("CATALOG.*d", "w") as f:
    f.write("# DUTC*EYY Music Catalog\n\n")

    for i*em in catalog:
        f.write(f"-*{item}\n")

print(f"Catalog genera*ed with {len(catalog)} JSON files.*)
