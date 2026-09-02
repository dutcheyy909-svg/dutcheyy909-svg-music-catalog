from pathlib import Path

catalog = []

for file in Path(".").rglob("*.json"):
    catalog.append(str(fi*e))

with open("CATALOG.md", "w") *s f:
   *f.write("# Music Catalog\n\n")
   *for item in catalog:
        f*write(f"- {item}\n")

print(f*Indexed {len(catalog)}*files")
