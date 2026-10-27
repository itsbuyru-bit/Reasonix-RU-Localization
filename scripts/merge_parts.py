"""Собирает перевод из work/ru_parts и проверяет его.

По умолчанию только отчёт. С --write пишет translations/ru.json.

Проверки:
  * пропуски (нет перевода);
  * лишние ключи, которых нет в каталоге;
  * конфликты (один ключ переведён по-разному в разных частях);
  * потерянные/лишние {плейсхолдеры};
  * строки, оставшиеся китайскими;
  * подозрительные пустые строки и переносы строк.
"""
import argparse
import collections
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths

PARTS = paths.PARTS
DICTIONARY = paths.RU_DICT
OVERRIDES = os.path.join(paths.TRANSLATIONS, "ru_overrides.json")


def load_parts():
    merged = {}
    conflicts = []
    sources = collections.defaultdict(list)
    for file in sorted(glob.glob(os.path.join(PARTS, "part_*.json"))):
        data = common.read_json(file, {})
        if not isinstance(data, dict):
            continue
        for zh, ru in data.items():
            if not isinstance(ru, str):
                continue
            sources[zh].append((os.path.basename(file), ru))
            if zh in merged and merged[zh] != ru:
                conflicts.append((zh, merged[zh], ru, os.path.basename(file)))
            else:
                merged[zh] = ru
    return merged, conflicts, sources


def main(argv=None):
    global PARTS, DICTIONARY, OVERRIDES
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="ru", help="код языка из languages/<code>.json")
    parser.add_argument("--write", action="store_true", help="записать словарь языка")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args(argv)

    profile = paths.load_profile(args.lang)
    PARTS = paths.parts_dir(profile["code"])
    DICTIONARY = paths.profile_dictionary(profile)
    OVERRIDES = paths.profile_overrides(profile)

    data = common.read_json(paths.SOURCE)
    if not data:
        raise SystemExit("Нет %s — сначала запустите scripts/extract_source.py" % paths.SOURCE)
    rows = data["rows"]
    source_keys = {row["zh"] for row in rows}

    parts, conflicts, _ = load_parts()
    overrides = common.read_json(OVERRIDES, {})
    if not isinstance(overrides, dict):
        overrides = {}
    result = {}
    missing = []
    for row in rows:
        zh = row["zh"]
        if zh in overrides and isinstance(overrides[zh], str) and overrides[zh].strip():
            result[zh] = overrides[zh]
        elif not common.needs_translation(zh):
            result[zh] = zh
        elif parts.get(zh, "").strip():
            result[zh] = parts[zh]
        else:
            missing.append(row)

    extra = sorted(set(parts) - source_keys)
    placeholder_bad = []
    untranslated = []
    suspicious = []
    empty = []

    for row in rows:
        zh = row["zh"]
        ru = result.get(zh, "")
        if not ru:
            empty.append(row)
            continue
        problems = common.placeholder_problems(zh, ru)
        if problems:
            placeholder_bad.append((zh, ru, problems))
        if common.looks_untranslated(zh, ru):
            untranslated.append((zh, ru, row.get("en", "")))
        if "\n" in ru or "\r" in ru:
            suspicious.append(("перенос строки", zh, ru))
        if ru != ru.strip():
            suspicious.append(("пробелы по краям", zh, repr(ru)))
        english = row.get("en") or ""
        if english and len(english) > 20:
            ratio = len(ru) / max(1, len(english))
            if ratio < 0.25 or ratio > 4.0:
                suspicious.append(("длина x%.2f" % ratio, zh, common.short(ru, 90)))

    common.log("Строк в каталоге:      %d" % len(rows))
    common.log("Переведено:            %d" % len(result))
    common.log("Осталось:              %d" % len(missing))
    common.log("Конфликтов:            %d" % len(conflicts))
    common.log("Лишних ключей:         %d" % len(extra))
    common.log("Плейсхолдеры:          %d" % len(placeholder_bad))
    common.log("Похоже на китайский:   %d" % len(untranslated))
    common.log("Подозрительных:        %d" % len(suspicious))

    if missing:
        common.log("\nПервые пропуски:")
        for row in missing[:20]:
            common.log("  - %s" % common.short(row["zh"], 70))
    if conflicts:
        common.log("\nКонфликты:")
        for zh, a, b, file in conflicts[:10]:
            common.log("  - %s: %r / %r (%s)" % (common.short(zh, 50), a, b, file))
    if placeholder_bad:
        common.log("\nОшибки плейсхолдеров:")
        for zh, ru, problems in placeholder_bad[:20]:
            common.log("  - %s -> %s [%s]" % (common.short(zh, 50), common.short(ru, 50), "; ".join(problems)))
    if untranslated:
        common.log("\nНе переведено (проверить вручную):")
        for zh, ru, en in untranslated[:20]:
            common.log("  - %s -> %s  (en: %s)" % (common.short(zh, 45), common.short(ru, 45), common.short(en, 45)))
    if suspicious:
        common.log("\nПодозрительные строки:")
        for reason, zh, ru in suspicious[:20]:
            common.log("  - [%s] %s -> %s" % (reason, common.short(zh, 45), common.short(ru, 60)))

    report = {
        "total": len(rows),
        "translated": len(result),
        "missing": [row["zh"] for row in missing],
        "conflicts": [{"zh": zh, "a": a, "b": b, "file": f} for zh, a, b, f in conflicts],
        "extra": extra,
        "placeholder_bad": [{"zh": zh, "ru": ru, "problems": p} for zh, ru, p in placeholder_bad],
        "untranslated": [{"zh": zh, "ru": ru, "en": en} for zh, ru, en in untranslated],
        "suspicious": [{"reason": r, "zh": zh, "ru": ru} for r, zh, ru in suspicious],
    }
    common.write_json(os.path.join(paths.WORK, "report.json"), report, indent=1)

    # Таблица для вычитки ключевых экранов.
    review_path = os.path.join(paths.WORK, "ru_review.tsv")
    with open(review_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("zh\ten\tru\n")
        for row in rows:
            zh = row["zh"]
            f.write(
                "%s\t%s\t%s\n"
                % (
                    zh.replace("\t", " ").replace("\n", "\\n"),
                    (row.get("en") or "").replace("\t", " ").replace("\n", "\\n"),
                    result.get(zh, "").replace("\t", " ").replace("\n", "\\n"),
                )
            )
    common.log("\nОтчёт: %s" % os.path.join(paths.WORK, "report.json"))
    common.log("Таблица для вычитки: %s" % review_path)

    fatal = bool(missing or conflicts or placeholder_bad)
    if args.write:
        if fatal and not args.allow_partial:
            common.log("\nНе записываю translations/ru.json: сначала устраните ошибки "
                       "(или используйте --allow-partial).")
            raise SystemExit(1)
        common.write_json(DICTIONARY, result, indent=0)
        common.log("\nЗаписано: %s (%d строк)" % (DICTIONARY, len(result)))

    if fatal:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
