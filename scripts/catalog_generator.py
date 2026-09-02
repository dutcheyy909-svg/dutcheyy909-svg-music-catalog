import os

print("Music Catalog Generator")

for root, dirs, files in os.walk("."):
    for file in files:
        print(os.path.join(root, file))
