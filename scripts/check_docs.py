"""Проверяет локальные ссылки и обязательные файлы документации."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["README.md", "README.ru.md", "CONTRIBUTING.md"]
for name in os.listdir(os.path.join(ROOT, "docs")):
    if name.endswith(".md"):
        FILES.append(os.path.join("docs", name))
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REQUIRED = [
    "LOCALIZE.bat",
    "LOCALIZE-RU.bat",
    "languages/ru-RU.json",
    "locale/ru-RU.json",
    "docs/ADDING-A-LANGUAGE.md",
    "docs/USING-THE-SKILL.md",
    "docs/TRANSLATION.md",
    "docs/TROUBLESHOOTING.md",
    "README.md",
    "README.ru.md",
]


def check():
    errors = []
    for rel in REQUIRED:
        if not os.path.isfile(os.path.join(ROOT, rel)):
            errors.append("нет обязательного файла: " + rel)
    for rel in FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        for raw in LINK.findall(text):
            target = raw.split("#", 1)[0].split("?", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            full = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(full):
                errors.append("%s -> %s" % (rel, raw))
    return errors


def main():
    errors = check()
    for error in errors:
        print("ERROR", error)
    print("docs: %d errors" % len(errors))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
