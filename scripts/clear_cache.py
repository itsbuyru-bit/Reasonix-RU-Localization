"""Сбрасывает кэш интерфейса Reasonix Studio.

Удаляются только кэши Chromium (Cache, Code Cache, GPUCache и т.п.).
Настройки, темы, сессии, localStorage и cookies не затрагиваются.

Запускать при полностью закрытом Reasonix Studio.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths

CACHE_DIRS = [
    "Cache",
    "Code Cache",
    "GPUCache",
    "DawnGraphiteCache",
    "DawnWebGPUCache",
    "ShaderCache",
    "GrShaderCache",
    "GPUPersistentCache",
]

PARTITION_CACHE_DIRS = ["Cache", "Code Cache", "GPUCache"]


def profile_root():
    appdata = os.environ.get("APPDATA") or os.path.join(
        os.path.expanduser("~"), "AppData", "Roaming"
    )
    return os.path.join(appdata, "Reasonix Studio")


def dir_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def clear_profile(profile, dry=False):
    """Удаляет кэши в одном профиле. Возвращает [(путь, байты)]."""
    removed = []
    for name in CACHE_DIRS:
        path = os.path.join(profile, name)
        if not os.path.isdir(path):
            continue
        size = dir_size(path)
        if not dry:
            shutil.rmtree(path, ignore_errors=True)
        removed.append((path, size))

    partitions = os.path.join(profile, "Partitions")
    if os.path.isdir(partitions):
        for entry in os.listdir(partitions):
            for name in PARTITION_CACHE_DIRS:
                path = os.path.join(partitions, entry, name)
                if not os.path.isdir(path):
                    continue
                size = dir_size(path)
                if not dry:
                    shutil.rmtree(path, ignore_errors=True)
                removed.append((path, size))
    return removed


def main():
    dry = "--dry-run" in sys.argv
    if paths.app_running():
        raise SystemExit(
            "Reasonix Studio запущен. Полностью закройте его (включая значок в трее) "
            "и повторите."
        )
    root = profile_root()
    if not os.path.isdir(root):
        raise SystemExit("Не найден каталог данных Reasonix Studio: " + root)

    profiles = [
        os.path.join(root, name)
        for name in os.listdir(root)
        if name.startswith("io.reasonix.studio.") and os.path.isdir(os.path.join(root, name))
    ]
    if not profiles:
        profiles = [root]

    total = 0
    for profile in profiles:
        removed = clear_profile(profile, dry=dry)
        if not removed:
            continue
        common.log(os.path.basename(profile))
        for path, size in removed:
            common.log("  %-24s %8.1f МБ" % (os.path.basename(path), size / 1024 / 1024))
            total += size
    common.log("")
    common.log(
        "%s %.1f МБ кэша."
        % ("Будет удалено" if dry else "Удалено", total / 1024 / 1024)
    )
    if dry:
        common.log("(dry-run: ничего не удалено)")


if __name__ == "__main__":
    main()
