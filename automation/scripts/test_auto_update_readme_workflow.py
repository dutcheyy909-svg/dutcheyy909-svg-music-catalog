import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "auto-update-readme.yml"


class AutoUpdateReadmeWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        cls.workflow = yaml.safe_load(workflow_text)

    def _get_push_config(self):
        workflow_on = self.workflow.get("on", self.workflow.get(True, {}))
        return workflow_on.get("push", {})

    def _get_steps(self):
        return self.workflow["jobs"]["update-readme"]["steps"]

    def test_workflow_exists(self):
        self.assertTrue(WORKFLOW_PATH.is_file())

    def test_workflow_triggers_on_push_to_main(self):
        self.assertEqual(self.workflow["name"], "Auto-Update README")
        self.assertEqual(self._get_push_config()["branches"], ["main"])

    def test_workflow_sets_up_python_and_generates_readme(self):
        steps = self._get_steps()
        self.assertEqual(steps[0]["uses"], "actions/checkout@v5")
        self.assertEqual(steps[1]["uses"], "actions/setup-python@v5")
        self.assertEqual(steps[1]["with"]["python-version"], "3.11")
        self.assertEqual(steps[3]["run"], "python automation/scripts/generate-readme.py")

    def test_workflow_commits_updated_readme(self):
        commit_step = self._get_steps()[4]["run"]
        self.assertIn("automation/scripts/requirements.txt", self._get_steps()[2]["run"])
        self.assertIn("git add README.md", commit_step)
        self.assertIn('git commit -m "Auto-update README"', commit_step)
        self.assertIn("git push", commit_step)


if __name__ == "__main__":
    unittest.main()
