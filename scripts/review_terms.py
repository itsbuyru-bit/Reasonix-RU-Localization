"""Отчёт по терминологии и подозрительным местам перевода.

Не меняет словарь. Пишет work/review_terms.json и печатает краткую сводку.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths
from merge_parts import OVERRIDES, load_parts

CYRILLIC = re.compile(r"[А-Яа-яЁё]")
CJK = re.compile(r"[\u4e00-\u9fff]")

TERM_CHECKS = [
    ("workbench", "верстак"),
    ("session", "сессия"),
    ("workspace", "рабочая область"),
    ("kernel", "ядро"),
    ("chat", "чат"),
    ("conversation", "беседа"),
    ("tool", "инструмент"),
    ("subagent", "субагент"),
    ("checkpoint", "контрольная точка"),
    ("sandbox", "песочница"),
    ("marketplace", "маркетплейс"),
]


def main():
    data = common.read_json(paths.SOURCE)
    rows = data["rows"]
    parts, conflicts, _ = load_parts()
    overrides = common.read_json(OVERRIDES, {})
    if not isinstance(overrides, dict):
        overrides = {}

    result = {}
    for row in rows:
        zh = row["zh"]
        if zh in overrides and isinstance(overrides[zh], str) and overrides[zh].strip():
            result[zh] = overrides[zh]
        elif not common.needs_translation(zh):
            result[zh] = zh
        elif parts.get(zh, "").strip():
            result[zh] = parts[zh]

    issues = collections.OrderedDict()
    issues["cjk_in_ru"] = []
    issues["capital_vy"] = []
    issues["double_space"] = []
    issues["edge_space"] = []
    issues["unbalanced_quotes"] = []
    issues["placeholder"] = []
    issues["short_label_period"] = []
    issues["length_ratio"] = []
    issues["term"] = []

    for row in rows:
        zh = row["zh"]
        ru = result.get(zh, "")
        if not ru:
            continue
        en = row.get("en") or ""
        if CJK.search(ru):
            issues["cjk_in_ru"].append((zh, ru))
        if re.search(r"(?<![А-Яа-яЁё])Вы(?![А-Яа-яЁё])", ru):
            issues["capital_vy"].append((zh, ru))
        if "  " in ru:
            issues["double_space"].append((zh, ru))
        if ru != ru.strip():
            issues["edge_space"].append((zh, repr(ru)))
        if ru.count("«") != ru.count("»"):
            issues["unbalanced_quotes"].append((zh, ru))
        problems = common.placeholder_problems(zh, ru)
        if problems:
            issues["placeholder"].append((zh, ru, "; ".join(problems)))
        if len(ru) <= 24 and ru.endswith(".") and en and not en.endswith("."):
            issues["short_label_period"].append((zh, ru, en))
        if en and len(en) > 20 and CYRILLIC.search(ru):
            ratio = len(ru) / max(1, len(en))
            if ratio < 0.3 or ratio > 3.5:
                issues["length_ratio"].append((zh, ru, en, round(ratio, 2)))
        low_en = en.lower()
        low_ru = ru.lower()
        for term, preferred in TERM_CHECKS:
            if term in low_en and preferred not in low_ru:
                issues["term"].append((term, preferred, zh, ru, en))
                break

    for name, items in issues.items():
        common.log("%-22s %d" % (name, len(items)))
        for item in items[:8]:
            common.log("  " + " | ".join(str(x)[:70] for x in item))

    if conflicts:
        common.log("conflicts              %d" % len(conflicts))
    report = {name: items for name, items in issues.items()}
    report["conflicts"] = conflicts
    common.write_json(
        os.path.join(paths.WORK, "review_terms.json"),
        report,
        indent=1,
    )
    common.log("\nОтчёт: %s" % os.path.join(paths.WORK, "review_terms.json"))


if __name__ == "__main__":
    main()
