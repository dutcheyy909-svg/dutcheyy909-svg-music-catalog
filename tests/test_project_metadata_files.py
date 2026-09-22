import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = REPO_ROOT / "music-catalog" / "projects"


class ProjectMetadataFileTests(unittest.TestCase):
    def test_project_ids_are_unique_when_normalized(self):
        normalized_project_ids = {}

        for project_file in sorted(PROJECTS_DIR.glob("*.json")):
            if project_file.name.endswith(".schema.json"):
                continue

            project_data = json.loads(project_file.read_text(encoding="utf-8"))
            normalized_project_id = project_data["project_id"].replace("_", "-")
            normalized_project_ids.setdefault(normalized_project_id, []).append(project_file.name)

        duplicates = {
            project_id: file_names
            for project_id, file_names in normalized_project_ids.items()
            if len(file_names) > 1
        }

        self.assertEqual(duplicates, {})


if __name__ == "__main__":
    unittest.main()
