"""Пути проекта «Русификация Reasonix Studio».

Все пути выводятся из расположения этого файла, поэтому проект можно
переносить целиком. Единственное, что берётся из системы, — каталог
установленного Reasonix Studio; его можно задать переменной окружения
REASONIX_STUDIO_DIR.
"""
import os

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS)

TRANSLATIONS = os.path.join(ROOT, "translations")
RU_DICT = os.path.join(TRANSLATIONS, "ru.json")
LANGUAGES = os.path.join(ROOT, "languages")
DEFAULT_LANG = "ru"
REFERENCE = os.path.join(ROOT, "reference")
FR_REFERENCE = os.path.join(REFERENCE, "fr.json")

WORK = os.path.join(ROOT, "work")
SOURCE = os.path.join(WORK, "source.json")
BUNDLE_DICT = os.path.join(WORK, "bundle_dict.json")
PARTS = os.path.join(WORK, "ru_parts")
BACKUP = os.path.join(WORK, "backup")
TEST = os.path.join(WORK, "test")
ASAR_WORK = os.path.join(WORK, "asar")
ASAR_TOOLS = os.path.join(WORK, "tools")
ASAR_JS = os.path.join(ASAR_TOOLS, "node_modules", "@electron", "asar", "lib", "asar.js")


def _localappdata():
    return os.environ.get("LOCALAPPDATA") or os.path.join(
        os.path.expanduser("~"), "AppData", "Local")


def _programfiles():
    return os.environ.get("ProgramFiles") or r"C:\Program Files"


def candidates():
    """Все места, где может лежать Reasonix Studio, в порядке приоритета."""
    forced = os.environ.get("REASONIX_STUDIO_DIR")
    if forced:
        yield os.path.abspath(forced)
    yield os.path.join(_localappdata(), "Programs", "Reasonix Studio")
    yield os.path.join(_localappdata(), "Reasonix Studio")
    for drive in "CDEFGH":
        yield os.path.join(drive + ":\\", "AI", "Reasonix Studio")
        yield os.path.join(drive + ":\\", "Reasonix Studio")
    yield os.path.join(_programfiles(), "Reasonix Studio")


def app_dir(required=True):
    for path in candidates():
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "resources", "app.asar")):
            return path
    if required:
        raise SystemExit(
            "Reasonix Studio не найден.\n"
            "Укажите каталог установки переменной окружения REASONIX_STUDIO_DIR,\n"
            "например:  set REASONIX_STUDIO_DIR=D:\\AI\\Reasonix Studio"
        )
    return None


def app_resources():
    return os.path.join(app_dir(), "resources")


def app_assets():
    return os.path.join(app_resources(), "frontend-next", "dist", "assets")


def app_dist():
    return os.path.join(app_resources(), "frontend-next", "dist")


def app_asar():
    return os.path.join(app_resources(), "app.asar")


def app_version():
    """Версия из package.json внутри app.asar (без внешних зависимостей)."""
    import json
    import struct

    path = app_asar()
    with open(path, "rb") as f:
        head = f.read(16)
        if len(head) < 16:
            return None
        header_size = struct.unpack("<I", head[4:8])[0]
        json_size = struct.unpack("<I", head[12:16])[0]
        f.seek(16)
        header = json.loads(f.read(json_size).decode("utf-8").rstrip("\x00"))
        node = header.get("files", {}).get("package.json")
        if not node:
            return None
        f.seek(8 + header_size + int(node["offset"]))
        raw = f.read(int(node["size"]))
    try:
        return json.loads(raw.decode("utf-8")).get("version")
    except Exception:
        return None


def i18n_bundle():
    """Бандл i18n, который реально подключён в index.html."""
    import glob
    import re

    index = os.path.join(app_dist(), "index.html")
    if os.path.isfile(index):
        html = open(index, encoding="utf-8").read()
        m = re.search(r"/(i18n-[A-Za-z0-9_\-]+\.js)", html)
        if m:
            p = os.path.join(app_assets(), m.group(1))
            if os.path.isfile(p):
                return p
    hits = glob.glob(os.path.join(app_assets(), "i18n-*.js"))
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise SystemExit("Не найден бандл i18n-*.js в " + app_assets())
    raise SystemExit("Найдено несколько бандлов i18n: " + ", ".join(os.path.basename(h) for h in hits))


def settings_bundle():
    import glob

    hits = glob.glob(os.path.join(app_assets(), "Settings-*.js"))
    if not hits:
        raise SystemExit("Не найден бандл Settings-*.js в " + app_assets())
    if len(hits) > 1:
        hits.sort(key=os.path.getmtime, reverse=True)
    return hits[0]


def ensure_work():
    for d in (WORK, PARTS, BACKUP, TEST, ASAR_WORK, ASAR_TOOLS):
        os.makedirs(d, exist_ok=True)


def profile_path(code):
    return os.path.join(LANGUAGES, code + ".json")


def load_profile(code=DEFAULT_LANG):
    import json

    path = profile_path(code)
    if not os.path.isfile(path):
        raise SystemExit("Языковой профиль не найден: %s" % path)
    with open(path, encoding="utf-8") as f:
        profile = json.load(f)
    for field in ("code", "display", "global", "dictionary", "native", "push"):
        if field not in profile:
            raise SystemExit("В профиле %s нет поля %s" % (path, field))
    if not str(profile["global"]).startswith("__"):
        raise SystemExit("Поле global в %s должно начинаться с __" % path)
    return profile


def list_profiles():
    profiles = []
    if not os.path.isdir(LANGUAGES):
        return profiles
    for name in sorted(os.listdir(LANGUAGES)):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        code = name[:-5]
        try:
            profiles.append(load_profile(code))
        except SystemExit:
            continue
    return profiles


def profile_dictionary(profile):
    return os.path.join(ROOT, profile["dictionary"])


def profile_overrides(profile):
    path = profile.get("overrides")
    return os.path.join(ROOT, path) if path else ""


def parts_dir(code):
    return os.path.join(WORK, code + "_parts")


def app_running():
    """Запущен ли Reasonix Studio (только Windows)."""
    import subprocess

    if os.name != "nt":
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Reasonix Studio.exe", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except Exception:
        return False
    return "Reasonix Studio.exe" in (result.stdout or "")
