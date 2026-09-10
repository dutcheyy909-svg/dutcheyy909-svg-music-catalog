import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = SCRIPT_DIR.parent
REPO_ROOT = AUTOMATION_DIR.parent

TEMPLATE_PATH = AUTOMATION_DIR / "templates" / "readme-template.md"
DATA_PATH = AUTOMATION_DIR / "templates" / "readme-data.json"
README_PATH = REPO_ROOT / "README.md"
PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")


def load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def load_sections() -> dict[str, str]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("README data must be a JSON object")

    non_string_entries = [
        key for key, value in data.items() if not isinstance(key, str) or not isinstance(value, str)
    ]
    if non_string_entries:
        raise ValueError("README data must be a flat object with string keys and values")

    return data


def render(template: str, data: dict[str, str]) -> str:
    placeholders = set(PLACEHOLDER_PATTERN.findall(template))
    keys = set(data.keys())

    missing = placeholders - keys
    extra = keys - placeholders
    if missing or extra:
        problems = []
        if missing:
            problems.append(f"missing keys: {sorted(missing)}")
        if extra:
            problems.append(f"unused keys: {sorted(extra)}")
        raise ValueError("Template/data mismatch: " + "; ".join(problems))

    rendered = template
    for key in placeholders:
        rendered = rendered.replace(f"{{{{{key}}}}}", str(data[key]))

    if PLACEHOLDER_PATTERN.search(rendered):
        raise ValueError("Template contains unresolved placeholders after rendering")

    return rendered


def main() -> None:
    template = load_template()
    data = load_sections()
    readme = render(template, data)
    README_PATH.write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
