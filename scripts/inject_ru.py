"""Добавляет русский язык в веб-интерфейс установленного Reasonix Studio.

Что делает:
  1. находит бандл i18n, который реально подключён в index.html;
  2. учит резолвер языка коду `ru`, добавляет русский словарь;
  3. добавляет пункт «Русский» в список языков в бандле Settings;
  4. правит язык экрана запуска в index.html;
  5. переводит push-уведомления PWA в push-sw.js;
  6. проверяет синтаксис и маркеры, делает резервные копии.

Примеры:
  py scripts/inject_ru.py --dry-run
  py scripts/inject_ru.py
  py scripts/inject_ru.py --restore
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths

BT = chr(96)
LANG = "ru"
GLOBAL = "__RU"
DISPLAY = "Русский"
BACKUP_ROOT = paths.BACKUP

PUSH_TEXT_OLD = """  en: {
    approval: ["An action needs your approval", "Reasonix on your computer is waiting for you."],
    input: ["The model is waiting for your answer", "Reasonix on your computer needs an answer to go on."],
    error: ["A turn ended with an error", "A turn on your computer did not finish."],
    other: ["Reasonix", "Something on your computer is waiting for you."],
  },"""

PUSH_TEXT_NEW = """  ru: {
    approval: ["Действие требует вашего подтверждения", "Reasonix на вашем компьютере ждёт вас."],
    input: ["Модель ждёт вашего ответа", "Reasonix на вашем компьютере не может продолжить без ответа."],
    error: ["Ход завершился ошибкой", "Один из ходов на вашем компьютере не завершился."],
    other: ["Reasonix", "На вашем компьютере что-то ждёт вас."],
  },
  en: {
    approval: ["An action needs your approval", "Reasonix on your computer is waiting for you."],
    input: ["The model is waiting for your answer", "Reasonix on your computer needs an answer to go on."],
    error: ["A turn ended with an error", "A turn on your computer did not finish."],
    other: ["Reasonix", "Something on your computer is waiting for you."],
  },"""

PUSH_LANG_OLD = """function describe(data) {
  const language = /^zh/i.test(self.navigator.language || "") ? "zh" : "en";"""

PUSH_LANG_NEW = """function pickLanguage() {
  const tags = [self.navigator.language, ...(self.navigator.languages || [])].filter(Boolean);
  for (const tag of tags) {
    const low = String(tag).toLowerCase();
    if (low.startsWith("zh") || low.startsWith("yue") || low.startsWith("cmn")) return "zh";
    if (low.startsWith("ru")) return "ru";
    if (low.startsWith("en")) return "en";
  }
  return "en";
}

function describe(data) {
  const language = pickLanguage();"""


def patches():
    return [
        (
            "R1_translate",
            "function O(e,t){let n=b[e]??e;",
            f"function O(e,t){{let n=(y==={BT}{LANG}{BT}?globalThis.{GLOBAL}?.[e]:void 0)??b[e]??e;",
        ),
        (
            "R2_resolve",
            f"return t==={BT}zh{BT}||t==={BT}en{BT}?t:w()",
            f"return t==={BT}zh{BT}||t==={BT}en{BT}||t==={BT}{LANG}{BT}?t:w()",
        ),
        (
            "R3_lang",
            f"document.documentElement.lang=y==={BT}zh{BT}?{BT}zh-CN{BT}:{BT}en{BT}",
            f"document.documentElement.lang=y==={BT}zh{BT}?{BT}zh-CN{BT}:"
            f"y==={BT}{LANG}{BT}?{BT}{LANG}{BT}:{BT}en{BT}",
        ),
        (
            "R4_adopt",
            f"function D(e){{let t=(e??{BT}{BT}).trim().toLowerCase(),n=localStorage.getItem(x);",
            f"function D(e){{if((localStorage.getItem(x)||{BT}{BT}).trim().toLowerCase()==={BT}{LANG}{BT})"
            f"return !1;let t=(e??{BT}{BT}).trim().toLowerCase(),n=localStorage.getItem(x);",
        ),
        (
            "R5_machine",
            f"function w(){{return T(navigator.languages?.[0]??navigator.language??{BT}{BT})"
            f"?{BT}zh{BT}:{BT}en{BT}}}",
            f"function w(){{let L=navigator.languages?.[0]??navigator.language??{BT}{BT};"
            f"return T(L)?{BT}zh{BT}:L.toLowerCase().startsWith({BT}{LANG}{BT})?{BT}{LANG}{BT}:{BT}en{BT}}}",
        ),
    ]


def push_patches():
    return [
        ("P1_ru_text", PUSH_TEXT_OLD, PUSH_TEXT_NEW),
        ("P2_language", PUSH_LANG_OLD, PUSH_LANG_NEW),
    ]


def backup(path, tag):
    version = paths.app_version() or "unknown"
    folder = os.path.join(BACKUP_ROOT, str(version))
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, "%s__%s" % (tag, os.path.basename(path)))
    # Первая копия — эталон для отката; повторные применения её не трогают.
    if not os.path.exists(dest):
        shutil.copy2(path, dest)
    return dest


def write_atomic(path, text):
    tmp = path + ".ru-tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(tmp, path)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def apply_replacements(text, reps, dry):
    changed = []
    for name, old, new in reps:
        count = text.count(old)
        if count != 1:
            common.log("  !! %s: найдено %d совпадений (нужно 1) — пропущено" % (name, count))
            continue
        text = text.replace(old, new, 1)
        changed.append(name)
        common.log("  ok %s" % name)
    return text, changed


def patch_i18n(path, dictionary, dry):
    text = read(path)
    payload = json.dumps(dictionary, ensure_ascii=False, separators=(",", ":"))

    if ";globalThis.%s=" % GLOBAL in text:
        if dry:
            common.log("  словарь уже есть; dry-run: обновление не записано (%d строк)" % len(dictionary))
            return text, ["dictionary_update"]
        pattern = re.compile(
            r";globalThis\.%s=\{.*?\};v\.%s=globalThis\.%s;" % (GLOBAL, LANG, GLOBAL),
            re.S,
        )
        new_block = ";globalThis.%s=%s;v.%s=globalThis.%s;" % (GLOBAL, payload, LANG, GLOBAL)
        if not pattern.search(text):
            raise SystemExit("Найден маркер __RU, но блок словаря не читается. Восстановите файл из backup.")
        text = pattern.sub(lambda _m: new_block, text, count=1)
        common.log("  словарь обновлён: %d строк" % len(dictionary))
        return text, ["dictionary_update"]

    if "globalThis.%s" % GLOBAL in text:
        raise SystemExit(
            "Бандл выглядит частично пропатченным (есть __RU без блока словаря). "
            "Восстановите его из work/backup и повторите."
        )

    orig = text
    text, changed = apply_replacements(text, patches(), dry)
    if len(changed) != len(patches()):
        raise SystemExit("Не все якоря i18n совпали — файл не изменён.")
    text = text + "\n;globalThis.%s=%s;v.%s=globalThis.%s;\n" % (GLOBAL, payload, LANG, GLOBAL)
    common.log("  ok R6_dictionary (%d строк)" % len(dictionary))
    changed.append("R6_dictionary")
    if dry:
        common.log("  dry-run: i18n не записан")
        return orig, changed
    return text, changed


def patch_settings(path, dry):
    text = read(path)
    correct = f"[{BT}{LANG}{BT},{BT}{DISPLAY}{BT}]"
    if correct in text:
        common.log("  пункт «%s» уже есть" % DISPLAY)
        return text, False

    # Ранняя версия патча добавляла пару без квадратных скобок:
    # селектор показывал отдельные «u» и «y». Исправляем на месте.
    broken = f",{BT}{LANG}{BT},{BT}{DISPLAY}{BT}]"
    if broken in text:
        if text.count(broken) != 1:
            raise SystemExit("Повреждённый пункт языка найден %d раз." % text.count(broken))
        text = text.replace(broken, f",{correct}]", 1)
        common.log("  исправлен повреждённый пункт «%s»" % DISPLAY)
        if dry:
            common.log("  dry-run: Settings не записан")
            return read(path), False
        return text, True

    old = f"{BT}zh{BT},{BT}中文{BT}],[{BT}en{BT},{BT}英文{BT}]"
    new = old + f",{correct}"
    if text.count(old) != 1:
        raise SystemExit("Не найден список языков в Settings (совпадений: %d)." % text.count(old))
    text = text.replace(old, new, 1)
    common.log("  ok R7_settings: добавлен пункт «%s»" % DISPLAY)
    if dry:
        common.log("  dry-run: Settings не записан")
        return read(path), False
    return text, True


def patch_index(path, dry):
    text = read(path)
    old = 'document.documentElement.lang = zh ? "zh-CN" : "en";'
    new = 'document.documentElement.lang = p === "ru" ? "ru" : (zh ? "zh-CN" : "en");'
    if new in text:
        common.log("  index.html уже пропатчен")
        return text, False
    if text.count(old) != 1:
        raise SystemExit("Не найден якорь языка в index.html (совпадений: %d)." % text.count(old))
    text = text.replace(old, new, 1)
    common.log("  ok R8_index: язык экрана запуска")
    if dry:
        common.log("  dry-run: index.html не записан")
        return read(path), False
    return text, True


def patch_push_sw(path, dry):
    text = read(path)
    if "ru: {" in text and "pickLanguage" in text:
        common.log("  push-sw.js уже пропатчен")
        return text, False
    orig = text
    for name, old, new in push_patches():
        count = text.count(old)
        if count != 1:
            raise SystemExit("push-sw.js: якорь %s найден %d раз (нужно 1)." % (name, count))
        text = text.replace(old, new, 1)
        common.log("  ok %s" % name)
    if dry:
        common.log("  dry-run: push-sw.js не записан")
        return orig, False
    return text, True


def restore():
    version = paths.app_version() or "unknown"
    folder = os.path.join(BACKUP_ROOT, str(version))
    if not os.path.isdir(folder):
        raise SystemExit("Резервных копий для версии %s нет: %s" % (version, folder))
    restored = []
    for file in sorted(glob.glob(os.path.join(folder, "*"))):
        name = os.path.basename(file)
        parts = name.split("__", 1)
        target_name = parts[1] if len(parts) == 2 else name
        if target_name in ("index.html", "push-sw.js"):
            target = os.path.join(paths.app_dist(), target_name)
        else:
            target = os.path.join(paths.app_assets(), target_name)
        if not os.path.isfile(target):
            continue
        shutil.copy2(file, target)
        restored.append((target_name, name))
    for target_name, backup_name in restored:
        common.log("восстановлен %s <- %s" % (target_name, backup_name))
    if not restored:
        common.log("Нечего восстанавливать.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", help="каталог установки Reasonix Studio")
    parser.add_argument("--dict", default=paths.RU_DICT, help="словарь ru.json")
    parser.add_argument("--backup-dir", help="каталог резервных копий (для тестов)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--allow-version-mismatch", action="store_true")
    args = parser.parse_args()

    global BACKUP_ROOT
    if args.backup_dir:
        BACKUP_ROOT = os.path.abspath(args.backup_dir)

    if args.app:
        os.environ["REASONIX_STUDIO_DIR"] = os.path.abspath(args.app)

    if args.restore:
        restore()
        return

    paths.ensure_work()
    version = paths.app_version() or "unknown"
    common.log("Reasonix Studio: %s" % paths.app_dir())
    common.log("Версия: %s" % version)
    if not str(version).startswith("2.47"):
        common.log(
            "! Версия %s не проверялась. Якоря будут проверены; "
            "при несовпадении скрипт остановится." % version
        )
    if paths.app_running():
        common.log("! Reasonix Studio запущен: изменения применятся после перезапуска.")

    dictionary = common.read_json(args.dict, {})
    if not dictionary:
        if args.dry_run:
            common.log("! Словарь не найден: dry-run проверяет только якоря")
            dictionary = {}
        else:
            raise SystemExit("Словарь пуст или не найден: " + args.dict)
    common.log("Словарь: %s (%d строк)" % (args.dict, len(dictionary)))

    i18n = paths.i18n_bundle()
    settings = paths.settings_bundle()
    index = os.path.join(paths.app_dist(), "index.html")
    push = os.path.join(paths.app_dist(), "push-sw.js")

    common.log("\n== i18n: %s" % os.path.basename(i18n))
    new_i18n, changes_i18n = patch_i18n(i18n, dictionary, args.dry_run)
    common.log("\n== Settings: %s" % os.path.basename(settings))
    new_settings, changes_settings = patch_settings(settings, args.dry_run)
    common.log("\n== index.html")
    new_index, changes_index = patch_index(index, args.dry_run)
    common.log("\n== push-sw.js")
    new_push, changes_push = patch_push_sw(push, args.dry_run)

    if args.dry_run:
        common.log("\nDry-run завершён, файлы не изменены.")
        return

    written = []
    if new_i18n != read(i18n):
        written.append(("i18n", i18n, new_i18n, "i18n"))
    if changes_settings and new_settings != read(settings):
        written.append(("Settings", settings, new_settings, "settings"))
    if changes_index and new_index != read(index):
        written.append(("index.html", index, new_index, "index"))
    if changes_push and new_push != read(push):
        written.append(("push-sw.js", push, new_push, "push"))

    for label, path, text, tag in written:
        if label != "index.html":
            # Проверяем уже новый текст во временном файле.
            os.makedirs(paths.TEST, exist_ok=True)
            tmp = os.path.join(paths.TEST, "new-%s.mjs" % tag)
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            result = subprocess.run(
                ["node", "--check", tmp],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            ) if shutil.which("node") else None
            if result is not None and result.returncode != 0:
                raise SystemExit("Синтаксис нового %s некорректен:\n%s" % (label, result.stderr))
            common.log("  синтаксис %s: OK" % label)
        b = backup(path, tag)
        write_atomic(path, text)
        common.log("  записан %s (backup: %s)" % (os.path.basename(path), os.path.basename(b)))

    # Финальная проверка установленных файлов.
    installed = read(i18n)
    checks = {
        "словарь __RU": ";globalThis.%s=" % GLOBAL in installed,
        "v.ru": "v.%s=globalThis.%s" % (LANG, GLOBAL) in installed,
        "пункт в Settings": ("%s%s%s,%s%s%s" % (BT, LANG, BT, BT, DISPLAY, BT)) in read(settings),
        "язык index.html": 'p === "ru"' in read(index),
        "push-уведомления": "ru: {" in read(push) and "pickLanguage" in read(push),
    }
    common.log("")
    for label, ok in checks.items():
        common.log("  %s %s" % ("OK " if ok else "!! ", label))
    if not all(checks.values()):
        raise SystemExit("Не все проверки прошли — смотрите сообщения выше.")

    common.log("\nГотово. Перезапустите Reasonix Studio и выберите: Настройки → Язык → %s" % DISPLAY)


if __name__ == "__main__":
    main()
