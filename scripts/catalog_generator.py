import os
from pathlib import Path

print("Music Catalog Generator")

for root, dirs, files in os.walk("."):
    for file in files:
        print(os.path.join(root, file))

catalog = []

for file in Path(".").rglob("*.json"):
    catalog.append(str(file))

with open("CATALOG.md", "w") as f:
    f.write("# DUTCHEYY Music Catalog\n\n")

    for item in catalog:
        f.write(f"- {item}\n")

print(f"Catalog generated with {len(catalog)} JSON files.")
