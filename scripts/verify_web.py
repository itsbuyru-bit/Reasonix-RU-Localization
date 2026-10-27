"""Интеграционная проверка веб-инъектора на КОПИИ приложения.

Копирует frontend-next/dist и app.asar в work/test/app, восстанавливает
исходные файлы из work/backup/<версия> (если они есть), запускает inject_ru.py
с отдельным тестовым каталогом backup и проверяет:
  * синтаксис и реальный перевод через ESM-импорт;
  * переключение ru/en/zh, плейсхолдеры;
  * пункт «Русский», index.html и push-уведомления;
  * откат через --restore.

Установленное приложение и его рабочие backup не изменяются.
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths

TEST_DICT = {
    "重命名聊天": "Переименовать чат",
    "聊天标题": "Название чата",
    "加宽浏览器": "Расширить браузер",
    "定位到你说的：{text}": "Перейти к сказанному: {text}",
}


def run(command, **kwargs):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **kwargs,
    )
    if result.returncode != 0:
        common.log(result.stdout)
        common.log(result.stderr)
        raise SystemExit("команда завершилась с ошибкой: " + " ".join(command))
    return result.stdout


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", help="каталог установки (по умолчанию найденный)")
    parser.add_argument("--dict", help="словарь для проверки (по умолчанию из профиля)")
    parser.add_argument("--lang", default="ru", help="код языка из languages/<code>.json")
    args = parser.parse_args()
    if args.app:
        os.environ["REASONIX_STUDIO_DIR"] = os.path.abspath(args.app)

    profile = paths.load_profile(args.lang)
    code = profile["code"]
    display = profile["display"]
    marker = "[`%s`,`%s`]" % (code, display)
    paths.ensure_work()
    test_app = os.path.join(paths.TEST, "app")
    test_backup = os.path.join(paths.TEST, "backup")
    for folder in (test_app, test_backup):
        if os.path.isdir(folder):
            shutil.rmtree(folder)
    os.makedirs(os.path.join(test_app, "resources"), exist_ok=True)

    common.log("Копирую frontend-next/dist и app.asar в %s" % test_app)
    shutil.copytree(
        os.path.join(paths.app_resources(), "frontend-next"),
        os.path.join(test_app, "resources", "frontend-next"),
    )
    shutil.copy2(paths.app_asar(), os.path.join(test_app, "resources", "app.asar"))

    dist = os.path.join(test_app, "resources", "frontend-next", "dist")
    assets = os.path.join(dist, "assets")
    index_html = open(os.path.join(dist, "index.html"), encoding="utf-8").read()
    match = re.search(r"/(i18n-[A-Za-z0-9_\-]+\.js)", index_html)
    if not match:
        raise SystemExit("в index.html не найден бандл i18n")
    bundles = [match.group(1)]
    settings = max(
        [name for name in os.listdir(assets)
         if name.startswith("Settings-") and name.endswith(".js")],
        key=lambda name: os.path.getmtime(os.path.join(assets, name)),
    )

    originals = {
        "i18n": os.path.join(assets, bundles[0]),
        "settings": os.path.join(assets, settings),
        "index": os.path.join(dist, "index.html"),
        "push": os.path.join(dist, "push-sw.js"),
    }

    # Восстанавливаем исходные файлы из версионных backup, если они есть:
    # так тест работает и на уже пропатченной установке.
    version = str(paths.app_version() or "unknown")
    real_backup = os.path.join(paths.BACKUP, version)
    for tag, target in originals.items():
        saved = os.path.join(real_backup, "%s__%s" % (tag, os.path.basename(target)))
        if os.path.isfile(saved):
            shutil.copy2(saved, target)
            common.log("  исходный %s взят из backup" % os.path.basename(target))

    pristine = (
        profile["global"] not in read(originals["i18n"])
        and marker not in read(originals["settings"])
        and code not in read(originals["index"])
        and "pickLanguage" not in read(originals["push"])
    )
    if not pristine:
        common.log("! Копия уже пропатчена, исходных backup нет — проверка отката будет пропущена")

    original_hashes = {tag: digest(target) for tag, target in originals.items()}

    dictionary = args.dict
    if not dictionary:
        dictionary = paths.profile_dictionary(profile)
        if not os.path.isfile(dictionary):
            dictionary = os.path.join(paths.TEST, "%s-test.json" % code)
            common.write_json(dictionary, TEST_DICT, indent=1)
    values = common.read_json(dictionary, {})

    common.log("\n== инъекция в копию")
    run(
        [sys.executable, os.path.join(paths.SCRIPTS, "inject_ru.py"),
         "--app", test_app, "--dict", dictionary, "--backup-dir", test_backup,
         "--allow-running", "--lang", args.lang]
    )

    bundle = originals["i18n"]
    common.log("\n== проверка ESM-бандла")
    key = "重命名聊天"
    expected = values.get(key, TEST_DICT[key])
    placeholder_key = "定位到你说的：{text}"
    run([
        "node",
        os.path.join(paths.SCRIPTS, "verify_bundle.mjs"),
        bundle,
        key,
        expected,
        placeholder_key,
        code,
    ])

    common.log("\n== проверка Settings, index.html и push-sw.js")
    if marker not in read(originals["settings"]):
        raise SystemExit("в Settings нет корректного пункта «%s»" % display)
    if code not in read(originals["index"]):
        raise SystemExit("index.html не пропатчен")
    if ("\"%s\": {" % code) not in read(originals["push"]) or "pickLanguage" not in read(originals["push"]):
        raise SystemExit("push-sw.js не пропатчен")
    common.log("  OK пункт «%s»" % display)
    common.log("  OK язык экрана запуска")
    common.log("  OK push-уведомления языка")

    if code == "ru":
        common.log("\n== проверка push-уведомлений")
        run(["node", os.path.join(paths.SCRIPTS, "verify_push_sw.mjs"), originals["push"]])
    else:
        common.log("\n== проверка push-уведомлений: пропущена для %s" % code)

    if pristine:
        common.log("\n== проверка отката")
        backup_dir = os.path.join(test_backup, version)
        for tag, target in originals.items():
            saved = os.path.join(backup_dir, "%s__%s" % (tag, os.path.basename(target)))
            if not os.path.isfile(saved):
                raise SystemExit("нет тестовой резервной копии: %s" % saved)
            if digest(saved) != original_hashes[tag]:
                raise SystemExit("резервная копия не совпадает с исходником: %s" % tag)
        common.log("  OK резервные копии совпадают с исходными файлами")

        run([sys.executable, os.path.join(paths.SCRIPTS, "inject_ru.py"),
             "--app", test_app, "--restore", "--backup-dir", test_backup,
             "--allow-running", "--lang", args.lang])
        for tag, target in originals.items():
            if digest(target) != original_hashes[tag]:
                raise SystemExit("откат не восстановил %s" % tag)
        common.log("  OK откат восстановил i18n, Settings, index.html и push-sw.js")

    common.log("\nВСЁ ПРОШЛО. Установленное приложение не изменялось.")


if __name__ == "__main__":
    main()
