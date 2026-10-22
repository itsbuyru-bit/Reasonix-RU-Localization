"""Общие helpers: JSON, плейсхолдеры, проверки."""
import json
import os
import re
import sys

# Консоль Windows по умолчанию может быть в cp1251: принудительно UTF-8,
# иначе русский и китайский текст падают с UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PLACEHOLDER = re.compile(r"\{([A-Za-z0-9_]+)\}")
CJK = re.compile(r"[\u4e00-\u9fff]")
FULLWIDTH = re.compile(r"[（）「」『』、，。：；！？…—·]")


def needs_translation(text):
    """Нужен ли перевод: есть буквы и при этом иероглифы/полноширинная пунктуация."""
    text = text or ""
    if not re.search(r"[A-Za-z\u4e00-\u9fff]", text):
        return False
    return bool(CJK.search(text) or FULLWIDTH.search(text))


def read_json(path, default=None):
    if not os.path.isfile(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data, indent=1):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
        f.write("\n")
    os.replace(tmp, path)


def placeholders(text):
    return sorted(set(PLACEHOLDER.findall(text or "")))


def placeholder_problems(source, target):
    a = placeholders(source)
    b = placeholders(target)
    if a == b:
        return []
    missing = [x for x in a if x not in b]
    extra = [x for x in b if x not in a]
    out = []
    if missing:
        out.append("потеряны: " + ", ".join("{%s}" % x for x in missing))
    if extra:
        out.append("лишние: " + ", ".join("{%s}" % x for x in extra))
    return out


def has_cyrillic(text):
    return bool(re.search(r"[А-Яа-яЁё]", text or ""))


def looks_untranslated(source, target):
    """Перевод пуст, совпадает с китайским исходником или не содержит кириллицы."""
    if not target:
        return True
    # Строки без букв (символы, числа, «…») переводить не нужно.
    if not re.search(r"[A-Za-z\u4e00-\u9fff]", source):
        return False
    # Исходник уже латинский/технический — перевод может совпадать с ним.
    if not re.search(r"[\u4e00-\u9fff]", source):
        return False
    if target == source:
        return True
    return not has_cyrillic(target)


def short(text, n=60):
    text = (text or "").replace("\n", "\\n")
    return text if len(text) <= n else text[: n - 1] + "…"


def log(msg=""):
    print(msg, flush=True)


def can_write_dir(path):
    """Проверяет, можно ли создать файл в каталоге (а не только прочитать его)."""
    import tempfile

    try:
        with tempfile.NamedTemporaryFile(dir=path, prefix=".rx-ru-", delete=True):
            return True
    except OSError:
        return False


def is_admin():
    """Запущен ли процесс с правами администратора (Windows)."""
    if os.name != "nt":
        return True
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return True


def permission_hint(folder):
    return (
        "Недостаточно прав для записи в:\n  %s\n\n"
        "Reasonix Studio установлен в защищённую папку (например, Program Files).\n"
        "Полностью закройте Studio и запустите LOCALIZE-RU.bat от имени администратора:\n"
        "правый клик по файлу → «Запуск от имени администратора».\n\n"
        "Файлы приложения не изменены." % folder
    )
