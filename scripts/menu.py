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
PACK_CODE = "ru"
PACK_DISPLAY = "Русский"
PACK_DICT = paths.RU_DICT
PROFILE = None

STRINGS = {
    "ru": {
        "title": "Локализация Reasonix Studio",
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
        "no_dict": "Словарь языка не найден или пуст.",
        "no_dict_hint": "Сначала соберите перевод: пункт 5 меню.",
        "dict_lines": "Словарь: %d строк",
        "running": "Reasonix Studio запущен.",
        "running_hint": "Полностью закройте его (включая значок в трее) и повторите.",
        "running_gate": "Reasonix Studio запущен.",
        "running_gate_hint": "Полностью закройте его (включая значок в трее), чтобы применить перевод.",
        "gate_choice": "Закройте Studio и нажмите Enter (0 — выход): ",
        "running_web": "Reasonix Studio запущен: изменения применятся после перезапуска.",
        "done": "Готово.",
        "restart": "Перезапустите Reasonix Studio и выберите: Настройки → Язык → Русский",
        "error": "Операция завершилась с ошибкой (код %s).",
        "press_enter": "Нажмите Enter, чтобы вернуться в меню...",
        "unknown_version": "неизвестна",
        "tool_note": "Примечание: служебный вывод Python-скриптов остаётся на русском.",
        "protected": "! Reasonix Studio установлен в защищённую папку. Для пунктов 1, 2 и 4 запустите LOCALIZE-RU.bat от имени администратора.",
        "rebuild_failed": "Перевод завершился с ошибками; повторный запуск досчитает пропуски.",
    },
    "en": {
        "title": "Reasonix Studio Localization",
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
        "running_gate": "Reasonix Studio is running.",
        "running_gate_hint": "Quit it completely (including the tray icon) before applying the localization.",
        "gate_choice": "Quit Studio and press Enter (0 to exit): ",
        "running_web": "Reasonix Studio is running: changes apply after a restart.",
        "done": "Done.",
        "restart": "Restart Reasonix Studio and choose: Settings → Language → Русский",
        "error": "The operation failed (exit code %s).",
        "press_enter": "Press Enter to return to the menu...",
        "unknown_version": "unknown",
        "tool_note": "Note: low-level diagnostic output from the Python tools remains in Russian.",
        "protected": "! Reasonix Studio is installed in a protected folder. For options 1, 2 and 4, run LOCALIZE-RU.bat as administrator.",
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
    data = common.read_json(PACK_DICT, {})
    if not data:
        common.log(msg("no_dict"))
        common.log(msg("no_dict_hint"))
        return False
    common.log(msg("dict_lines", len(data)))
    return True


def ensure_closed_at_start():
    while paths.app_running():
        common.log(msg("running_gate"))
        common.log(msg("running_gate_hint"))
        try:
            answer = input(msg("gate_choice")).strip()
        except (EOFError, KeyboardInterrupt):
            return False
        if answer == "0":
            return False
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
    code = run("inject.py", "--lang", PACK_CODE)
    if code != 0:
        return code
    return run("patch_asar.py", "--lang", PACK_CODE, "--install")


def apply_web():
    if not dictionary_ready():
        return 1
    if paths.app_running():
        common.log(msg("running_web"))
    return run("inject.py", "--lang", PACK_CODE)


def verify():
    code = run("verify_web.py", "--lang", PACK_CODE)
    if code != 0:
        return code
    return run("patch_asar.py", "--lang", PACK_CODE, "--dry-run")


def restore():
    if not require_closed():
        return 1
    code = run("inject.py", "--lang", PACK_CODE, "--restore")
    if code != 0:
        return code
    return run("patch_asar.py", "--lang", PACK_CODE, "--restore")


def rebuild():
    code = run("extract_source.py")
    if code != 0:
        return code
    code = run("translate_api.py", "--lang", PACK_CODE, "--batch", "20", "--workers", "6")
    if code != 0:
        common.log(msg("rebuild_failed"))
        return code
    code = run("merge_parts.py", "--lang", PACK_CODE, "--write")
    if code != 0:
        return code
    return run("verify_web.py", "--lang", PACK_CODE)


def clear_cache():
    if not require_closed():
        return 1
    return run("clear_cache.py")


def option_value(argv, name, default):
    for i, arg in enumerate(argv):
        if arg == name and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith(name + "="):
            return arg.split("=", 1)[1]
    return default


def choose_pack(argv):
    explicit = option_value(argv, "--lang", None)
    if explicit:
        return paths.load_profile(explicit)
    profiles = paths.list_profiles()
    if not profiles:
        return paths.load_profile("ru")
    if len(profiles) == 1:
        return profiles[0]
    common.log("Языковой пакет / Language pack:")
    for index, profile in enumerate(profiles, 1):
        common.log("  %d. %s (%s)" % (index, profile["display"], profile["code"]))
    try:
        answer = input("Выбор / Choice [1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        answer = ""
    for profile in profiles:
        if answer == profile["code"]:
            return profile
    if answer.isdigit() and 1 <= int(answer) <= len(profiles):
        return profiles[int(answer) - 1]
    return profiles[0]


def main():
    global PACK_CODE, PACK_DISPLAY, PACK_DICT, PROFILE
    argv = sys.argv[1:]
    profile = choose_pack(argv)
    PROFILE = profile
    PACK_CODE = profile["code"]
    PACK_DISPLAY = profile["display"]
    PACK_DICT = paths.profile_dictionary(profile)
    choose_language(argv)
    common.log("=" * 52)
    common.log("  " + msg("title"))
    common.log("=" * 52)
    if LANG == "en":
        common.log(msg("tool_note"))
    try:
        common.log("%s: %s" % (msg("install"), paths.app_dir()))
        common.log("%s:    %s" % (msg("version"), paths.app_version() or msg("unknown_version")))
        if not common.is_admin() and not common.can_write_dir(paths.app_assets()):
            common.log(msg("protected"))
    except SystemExit as error:
        common.log(str(error))
        return 1
    common.log("%s:   %s" % (msg("dictionary"), PACK_DICT))

    if not ensure_closed_at_start():
        return 0

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
            common.log(msg("restart").replace("Русский", PACK_DISPLAY))
        else:
            common.log("\n" + msg("error", code))
        input("\n" + msg("press_enter"))


if __name__ == "__main__":
    raise SystemExit(main())
