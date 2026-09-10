import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "automation" / "scripts" / "generate-readme.py"


spec = importlib.util.spec_from_file_location("generate_readme", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GenerateReadmeTests(unittest.TestCase):
    def test_render_raises_on_template_data_mismatch(self):
        with self.assertRaises(ValueError):
            module.render("# {{project_name}}\n{{overview}}", {"project_name": "x"})

    def test_render_raises_on_unused_data_key(self):
        with self.assertRaises(ValueError):
            module.render("# {{project_name}}", {"project_name": "x", "overview": "y"})

    def test_main_writes_readme_from_non_repo_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            template_path = temp_path / "readme-template.md"
            data_path = temp_path / "readme-data.json"
            output_path = temp_path / "README.md"

            template_path.write_text("# {{project_name}}\n\n{{overview}}\n", encoding="utf-8")
            data_path.write_text(
                '{"project_name": "Repo", "overview": "Generated from template"}',
                encoding="utf-8",
            )

            original_template = module.TEMPLATE_PATH
            original_data = module.DATA_PATH
            original_output = module.README_PATH
            original_cwd = Path.cwd()
            try:
                module.TEMPLATE_PATH = template_path
                module.DATA_PATH = data_path
                module.README_PATH = output_path
                os.chdir(temp_path)
                module.main()
            finally:
                os.chdir(original_cwd)
                module.TEMPLATE_PATH = original_template
                module.DATA_PATH = original_data
                module.README_PATH = original_output

            self.assertEqual(output_path.read_text(encoding="utf-8"), "# Repo\n\nGenerated from template\n")


if __name__ == "__main__":
    unittest.main()
