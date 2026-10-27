"""Русифицирует нативные строки Reasonix Studio (resources/app.asar).

Патчит только копию: исходный app.asar не меняется, пока не указан --install.

Что переводится: экран запуска, контекстное меню, диалоги ошибок, диалог
старой версии и меню в трее. Якоря проверены на 2.47.1, 2.52.0 и 2.53.1.

Примеры:
  py scripts/vendor_asar.py
  py scripts/patch_asar_ru.py --dry-run
  py scripts/patch_asar_ru.py --install
  py scripts/patch_asar_ru.py --restore
"""
import argparse
import datetime
import glob
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import native_strings
import paths

FILES = ["uilang.js", "starting.js", "editmenu.js", "hostexit.js", "shelllog.js",
         "packagegrants.js", "main.js", "tray.js"]


def run_node(*args):
    node = shutil.which("node") or "node"
    result = subprocess.run(
        [node] + list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise SystemExit("node: %s" % ((result.stderr or result.stdout).strip()))
    return result.stdout


def asar_call(action, *args):
    helper = os.path.join(paths.SCRIPTS, "asar_tool.mjs")
    return run_node(helper, paths.ASAR_JS, action, *args)


def ensure_tool():
    if not os.path.isfile(paths.ASAR_JS):
        vendor = os.path.join(paths.SCRIPTS, "vendor_asar.py")
        result = subprocess.run(
            [sys.executable, vendor],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        common.log(result.stdout.strip())
        if result.returncode != 0:
            common.log(result.stderr.strip())
            raise SystemExit("Сначала установите @electron/asar: py scripts/vendor_asar.py")


def clean_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def apply_patches(src):
    missed = []
    for item in native_strings.PATCHES:
        path = os.path.join(src, "src", item["file"])
        if not os.path.isfile(path):
            missed.append((item["file"], "файл", 0))
            continue
        text = open(path, encoding="utf-8").read()
        for tag, old, new in item["reps"]:
            count = text.count(old)
            if count != 1:
                missed.append((item["file"], tag, count))
                continue
            text = text.replace(old, new, 1)
            common.log("  ok %-16s %s" % (item["file"], tag))
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    return missed


def check_syntax(src):
    for name in FILES:
        path = os.path.join(src, "src", name)
        result = subprocess.run(
            ["node", "--check", path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise SystemExit("Синтаксис %s некорректен:\n%s" % (name, result.stderr))
    common.log("  синтаксис: OK (%d файлов)" % len(FILES))


def verify(src):
    checks = {
        "uilang.js: ru": ("uilang.js", "isRussian"),
        "starting.js: ru": ("starting.js", "TEXT.ru"),
        "editmenu.js: Правка": ("editmenu.js", "Правка"),
        "hostexit.js: ядро": ("hostexit.js", "В прошлый раз ядро"),
        "shelllog.js: журналы": ("shelllog.js", "Журналы находятся"),
        "packagegrants.js: окно": ("packagegrants.js", "не удалось открыть окно"),
        "main.js: корзина": ("main.js", "Переместить в корзину"),
        "tray.js: выход": ("tray.js", "Выйти из Reasonix"),
    }
    ok = True
    for label, (name, needle) in checks.items():
        path = os.path.join(src, "src", name)
        text = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
        good = needle in text
        common.log("  %s %s" % ("OK " if good else "!! ", label))
        ok = ok and good
    return ok


def backup_asar():
    os.makedirs(paths.BACKUP, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(paths.BACKUP, "%s__app.asar" % stamp)
    shutil.copy2(paths.app_asar(), dest)
    return dest


def restore():
    if paths.app_running():
        raise SystemExit("Закройте Reasonix Studio полностью, затем повторите --restore.")
    target_dir = os.path.dirname(paths.app_asar())
    if not common.can_write_dir(target_dir):
        raise SystemExit(common.permission_hint(target_dir))
    files = sorted(glob.glob(os.path.join(paths.BACKUP, "*__app.asar")), key=os.path.getmtime, reverse=True)
    if not files:
        raise SystemExit("Резервных копий app.asar нет: " + paths.BACKUP)
    target = paths.app_asar()
    shutil.copy2(files[0], target)
    common.log("Восстановлен app.asar <- %s" % os.path.basename(files[0]))


def install(packed):
    if paths.app_running():
        raise SystemExit(
            "Reasonix Studio запущен. Закройте его полностью (включая значок в трее), "
            "затем повторите --install."
        )
    target_dir = os.path.dirname(paths.app_asar())
    if not common.can_write_dir(target_dir):
        raise SystemExit(common.permission_hint(target_dir))
    backup = backup_asar()
    staged = paths.app_asar() + ".ru-new"
    shutil.copy2(packed, staged)
    try:
        os.replace(staged, paths.app_asar())
    except PermissionError:
        try:
            os.remove(staged)
        except OSError:
            pass
        raise SystemExit(
            "app.asar заблокирован. Закройте Reasonix Studio полностью и повторите --install."
        )
    common.log("app.asar заменён (backup: %s)" % os.path.basename(backup))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", help="каталог установки Reasonix Studio")
    parser.add_argument("--dry-run", action="store_true", help="собрать, проверить, не устанавливать")
    parser.add_argument("--install", action="store_true", help="заменить app.asar (нужно закрыть приложение)")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--allow-version-mismatch", action="store_true")
    args = parser.parse_args()

    if args.app:
        os.environ["REASONIX_STUDIO_DIR"] = os.path.abspath(args.app)

    if args.restore:
        restore()
        return

    paths.ensure_work()
    version = paths.app_version() or "unknown"
    common.log("Reasonix Studio: %s" % paths.app_dir())
    common.log("Версия: %s" % version)
    if not (str(version).startswith("2.47") or str(version).startswith("2.52") or str(version).startswith("2.53")):
        common.log(
            "! Версия %s не проверялась. Якоря будут проверены; "
            "при несовпадении скрипт остановится." % version
        )
    if paths.app_running():
        common.log("! Reasonix Studio запущен: сборка возможна, установка — только после закрытия.")

    ensure_tool()
    orig = os.path.join(paths.ASAR_WORK, "orig")
    ru = os.path.join(paths.ASAR_WORK, "ru")
    check = os.path.join(paths.ASAR_WORK, "check")
    packed = os.path.join(paths.ASAR_WORK, "app-ru.asar")

    common.log("\n== распаковка app.asar")
    clean_dir(orig)
    asar_call("extract", paths.app_asar(), orig)
    common.log("  файлов: %d" % sum(len(files) for _, _, files in os.walk(orig)))

    common.log("\n== применение русских строк")
    clean_dir(ru)
    shutil.copytree(orig, ru, dirs_exist_ok=True)
    missed = apply_patches(ru)
    if missed:
        common.log("\nНЕ НАЙДЕНЫ ЯКОРЯ:")
        for name, tag, count in missed:
            common.log("  %-18s %-12s %d" % (name, tag, count))
        raise SystemExit("Патч не применён: изменилась версия или сборка.")

    common.log("\n== проверка")
    check_syntax(ru)
    if not verify(ru):
        raise SystemExit("Проверка маркеров не прошла.")

    common.log("\n== сборка app-ru.asar")
    if os.path.exists(packed):
        os.remove(packed)
    asar_call("pack", ru, packed)
    common.log("  размер: %d байт" % os.path.getsize(packed))

    # Проверяем уже собранный архив, а не рабочую копию.
    clean_dir(check)
    asar_call("extract", packed, check)
    common.log("\n== проверка собранного архива")
    if not verify(check):
        raise SystemExit("Собранный app.asar не прошёл проверку.")

    if args.install:
        install(packed)
        common.log("\nГотово. Запустите Reasonix Studio и выберите русский язык.")
    else:
        common.log("\nСобранный архив: %s" % packed)
        common.log("Установка не выполнялась. Чтобы применить: py scripts/patch_asar_ru.py --install")
        common.log("Перед установкой полностью закройте Reasonix Studio.")


if __name__ == "__main__":
    main()
