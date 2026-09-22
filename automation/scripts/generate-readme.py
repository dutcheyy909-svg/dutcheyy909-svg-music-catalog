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


def _stringify_value(value):
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "\n".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def load_sections() -> dict[str, str]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("README data must be a JSON object")

    normalized: dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            raise ValueError("README data must have string keys")
        normalized[key] = _stringify_value(value)

    return normalized


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

    output = []
    cursor = 0
    for match in PLACEHOLDER_PATTERN.finditer(template):
        output.append(template[cursor:match.start()])
        output.append(data[match.group(1)])
        cursor = match.end()
    output.append(template[cursor:])
    return "".join(output)


def main() -> None:
    template = load_template()
    data = load_sections()
    readme = render(template, data)
    README_PATH.write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
