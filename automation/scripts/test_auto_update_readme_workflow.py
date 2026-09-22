import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "auto-update-readme.yml"


class AutoUpdateReadmeWorkflowTests(unittest.TestCase):
    def test_workflow_exists(self):
        self.assertTrue(WORKFLOW_PATH.is_file())

    def test_workflow_contains_issue_required_steps(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("name: Auto-Update README", workflow)
        self.assertIn("push:", workflow)
        self.assertIn("- main", workflow)
        self.assertIn("uses: actions/checkout@", workflow)
        self.assertIn("uses: actions/setup-python@", workflow)
        self.assertIn("python-version: \"3.11\"", workflow)
        self.assertIn("automation/scripts/requirements.txt", workflow)
        self.assertIn("python automation/scripts/generate-readme.py", workflow)
        self.assertIn("git add README.md", workflow)
        self.assertIn('git commit -m "Auto-update README"', workflow)
        self.assertIn("git push", workflow)


if __name__ == "__main__":
    unittest.main()
