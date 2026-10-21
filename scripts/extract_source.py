"""Извлекает исходные строки из установленного Reasonix Studio.

Результат — work/source.json: массив
    {"zh": "<китайский ключ>", "en": "<английский эталон>", "fr": "<французский эталон>"}

Ключом словаря в приложении является сам китайский текст. Английский эталон
берётся из бандла i18n текущей установки, французский — из reference/fr.json
(он же добавляет 16 строк, для которых в сборке ещё нет английского).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths


def main():
    paths.ensure_work()
    bundle = paths.i18n_bundle()
    version = paths.app_version() or "unknown"
    common.log("Reasonix Studio: %s" % paths.app_dir())
    common.log("Версия: %s" % version)
    common.log("Бандл: %s" % os.path.basename(bundle))

    node = os.environ.get("NODE") or "node"
    helper = os.path.join(paths.SCRIPTS, "extract_bundle.mjs")
    result = subprocess.run(
        [node, helper, bundle, paths.BUNDLE_DICT],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        common.log(result.stdout)
        common.log(result.stderr)
        raise SystemExit("Не удалось извлечь словарь из бандла")
    if result.stderr.strip():
        common.log(result.stderr.strip())

    bundle_dict = common.read_json(paths.BUNDLE_DICT, {})
    en = bundle_dict.get("en", {})
    zh = bundle_dict.get("zh", {})
    reference = common.read_json(paths.FR_REFERENCE, {})

    # Порядок: сначала строки французского эталона (он полный для 2.47.x),
    # затем всё, что встретилось в бандле, но отсутствует в эталоне.
    keys = list(reference.keys())
    seen = set(keys)
    for key in list(en.keys()) + list(zh.keys()):
        if key not in seen:
            seen.add(key)
            keys.append(key)

    rows = []
    missing_en = []
    for key in keys:
        english = en.get(key, "")
        if not english:
            missing_en.append(key)
        rows.append({"zh": key, "en": english, "fr": reference.get(key, "")})

    data = {
        "app_dir": paths.app_dir(),
        "app_version": version,
        "bundle": os.path.basename(bundle),
        "catalog": os.path.splitext(os.path.basename(bundle))[0],
        "count": len(rows),
        "rows": rows,
    }
    common.write_json(paths.SOURCE, data)

    common.log("")
    common.log("Строк всего: %d" % len(rows))
    common.log("Без английского эталона: %d" % len(missing_en))
    for key in missing_en[:20]:
        common.log("  - " + common.short(key, 80))
    common.log("Записано: %s" % paths.SOURCE)


if __name__ == "__main__":
    main()
