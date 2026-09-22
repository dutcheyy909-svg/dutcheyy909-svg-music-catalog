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

    def _find_step_by_uses(self, action):
        for step in self._get_steps():
            if step.get("uses") == action:
                return step
        self.fail(f"Expected step using {action!r}")

    def _find_step_containing_run(self, text):
        for step in self._get_steps():
            if text in step.get("run", ""):
                return step
        self.fail(f"Expected step containing run text {text!r}")

    def test_workflow_exists(self):
        self.assertTrue(WORKFLOW_PATH.is_file())

    def test_workflow_triggers_on_push_to_main(self):
        self.assertEqual(self.workflow["name"], "Auto-Update README")
        self.assertEqual(self._get_push_config()["branches"], ["main"])

    def test_workflow_sets_up_python_and_generates_readme(self):
        self.assertEqual(self._find_step_by_uses("actions/checkout@v5")["name"], "Checkout repository")
        setup_python_step = self._find_step_by_uses("actions/setup-python@v5")
        self.assertEqual(setup_python_step["with"]["python-version"], "3.11")
        self.assertEqual(
            self._find_step_containing_run("python automation/scripts/generate-readme.py")["name"],
            "Generate README",
        )

    def test_workflow_commits_updated_readme(self):
        install_step = self._find_step_containing_run("automation/scripts/requirements.txt")
        self.assertEqual(install_step["name"], "Install dependencies")

        commit_step = self._find_step_containing_run("git add README.md")["run"]
        self.assertIn('git commit -m "Auto-update README"', commit_step)
        self.assertIn("git push", commit_step)


if __name__ == "__main__":
    unittest.main()
