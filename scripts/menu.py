"""Bilingual menu for the Reasonix Studio Russian localization.

Russian is the default; English can be selected at startup or with --en.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
LANG = "ru"

STRINGS = {
    "ru": {
        "title": "Русификация Reasonix Studio",
        "install": "Установка",
        "version": "Версия",
        "dictionary": "Словарь",
        "menu": [
            "1. Применить полностью (интерфейс + нативные строки)",
            "2. Только веб-интерфейс",
            "3. Проверить на копии, ничего не менять",
            "4. Откатить изменения",
            "5. Пересобрать перевод из установленной версии (после обновления)",
            "6. Сбросить кэш интерфейса (если настройки не обновились)",
            "7. Выход",
        ],
        "choice": "Выбор: ",
        "invalid": "Нет такого пункта.",
        "no_dict": "Словарь translations/ru.json не найден или пуст.",
        "no_dict_hint": "Сначала соберите перевод: пункт 5 меню.",
        "dict_lines": "Словарь: %d строк",
        "running": "Reasonix Studio запущен.",
        "running_hint": "Полностью закройте его (включая значок в трее) и повторите.",
        "running_web": "Reasonix Studio запущен: изменения применятся после перезапуска.",
        "done": "Готово.",
        "restart": "Перезапустите Reasonix Studio и выберите: Настройки → Язык → Русский",
        "error": "Операция завершилась с ошибкой (код %s).",
        "press_enter": "Нажмите Enter, чтобы вернуться в меню...",
        "unknown_version": "неизвестна",
        "tool_note": "Примечание: служебный вывод Python-скриптов остаётся на русском.",
        "rebuild_failed": "Перевод завершился с ошибками; повторный запуск досчитает пропуски.",
    },
    "en": {
        "title": "Reasonix Studio Russian Localization",
        "install": "Install",
        "version": "Version",
        "dictionary": "Dictionary",
        "menu": [
            "1. Apply everything (interface + native strings)",
            "2. Web interface only",
            "3. Verify on a copy (no changes)",
            "4. Roll back changes",
            "5. Rebuild the translation from the installed version (after an update)",
            "6. Clear the interface cache (if settings did not update)",
            "7. Exit",
        ],
        "choice": "Choice: ",
        "invalid": "No such option.",
        "no_dict": "translations/ru.json is missing or empty.",
        "no_dict_hint": "Build the translation first: menu option 5.",
        "dict_lines": "Dictionary: %d strings",
        "running": "Reasonix Studio is running.",
        "running_hint": "Quit it completely (including the tray icon) and try again.",
        "running_web": "Reasonix Studio is running: changes apply after a restart.",
        "done": "Done.",
        "restart": "Restart Reasonix Studio and choose: Settings → Language → Русский",
        "error": "The operation failed (exit code %s).",
        "press_enter": "Press Enter to return to the menu...",
        "unknown_version": "unknown",
        "tool_note": "Note: low-level diagnostic output from the Python tools remains in Russian.",
        "rebuild_failed": "The translation finished with errors; run it again to retry the missing strings.",
    },
}


def msg(key, *args):
    value = STRINGS[LANG][key]
    if args:
        return value % args
    return value


def choose_language(argv):
    global LANG
    if "--en" in argv:
        LANG = "en"
        return
    if "--ru" in argv:
        LANG = "ru"
        return
    common.log("Язык / Language:")
    common.log("  1. Русский (по умолчанию)")
    common.log("  2. English")
    try:
        choice = input("Выбор / Choice [1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = ""
    LANG = "en" if choice == "2" else "ru"


def run(script, *args):
    command = [sys.executable, os.path.join(SCRIPTS, script)] + list(args)
    common.log("\n> " + " ".join(command))
    return subprocess.call(command)


def dictionary_ready():
    data = common.read_json(paths.RU_DICT, {})
    if not data:
        common.log(msg("no_dict"))
        common.log(msg("no_dict_hint"))
        return False
    common.log(msg("dict_lines", len(data)))
    return True


def require_closed():
    if paths.app_running():
        common.log(msg("running"))
        common.log(msg("running_hint"))
        return False
    return True


def apply_full():
    if not dictionary_ready() or not require_closed():
        return 1
    code = run("inject_ru.py")
    if code != 0:
        return code
    return run("patch_asar_ru.py", "--install")


def apply_web():
    if not dictionary_ready():
        return 1
    if paths.app_running():
        common.log(msg("running_web"))
    return run("inject_ru.py")


def verify():
    code = run("verify_web.py")
    if code != 0:
        return code
    return run("patch_asar_ru.py", "--dry-run")


def restore():
    if not require_closed():
        return 1
    code = run("inject_ru.py", "--restore")
    if code != 0:
        return code
    return run("patch_asar_ru.py", "--restore")


def rebuild():
    code = run("extract_source.py")
    if code != 0:
        return code
    code = run("translate_api.py", "--batch", "20", "--workers", "6")
    if code != 0:
        common.log(msg("rebuild_failed"))
        return code
    code = run("merge_parts.py", "--write")
    if code != 0:
        return code
    return run("verify_web.py")


def clear_cache():
    if not require_closed():
        return 1
    return run("clear_cache.py")


def main():
    choose_language(sys.argv[1:])
    common.log("=" * 52)
    common.log("  " + msg("title"))
    common.log("=" * 52)
    if LANG == "en":
        common.log(msg("tool_note"))
    try:
        common.log("%s: %s" % (msg("install"), paths.app_dir()))
        common.log("%s:    %s" % (msg("version"), paths.app_version() or msg("unknown_version")))
    except SystemExit as error:
        common.log(str(error))
        return 1
    common.log("%s:   %s" % (msg("dictionary"), paths.RU_DICT))

    while True:
        common.log("")
        for line in msg("menu"):
            common.log(line)
        try:
            choice = input(msg("choice")).strip()
        except (EOFError, KeyboardInterrupt):
            common.log("")
            return 0

        if choice == "1":
            code = apply_full()
        elif choice == "2":
            code = apply_web()
        elif choice == "3":
            code = verify()
        elif choice == "4":
            code = restore()
        elif choice == "5":
            code = rebuild()
        elif choice == "6":
            code = clear_cache()
        elif choice == "7":
            return 0
        else:
            common.log(msg("invalid"))
            continue

        if code == 0:
            common.log("\n" + msg("done"))
            common.log(msg("restart"))
        else:
            common.log("\n" + msg("error", code))
        input("\n" + msg("press_enter"))


if __name__ == "__main__":
    raise SystemExit(main())
