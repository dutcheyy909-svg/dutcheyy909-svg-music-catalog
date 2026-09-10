import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = SCRIPT_DIR.parent
REPO_ROOT = AUTOMATION_DIR.parent

TEMPLATE_PATH = AUTOMATION_DIR / "templates" / "readme-template.md"
DATA_PATH = AUTOMATION_DIR / "templates" / "readme-data.json"
README_PATH = REPO_ROOT / "README.md"


def load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def load_sections() -> dict[str, str]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def render(template: str, data: dict[str, str]) -> str:
    rendered = template
    for key, value in data.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def main() -> None:
    template = load_template()
    data = load_sections()
    readme = render(template, data)
    README_PATH.write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
