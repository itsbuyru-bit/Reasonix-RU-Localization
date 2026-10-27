"""Проверяет языковой профиль и словарь перед PR.

Примеры:
  python scripts/validate_language_pack.py
  python scripts/validate_language_pack.py --lang de-DE
  python scripts/validate_language_pack.py --lang _template --allow-partial
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import native_patches
import paths

TEMPLATE = os.path.join(paths.LANGUAGES, "..", "locale", "_template.json")
CODE_RE = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
GLOBAL_RE = re.compile(r"^__[A-Z0-9_]+$")
IDENT_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
NATIVE_SECTIONS = {
    "uilang": ("checker",),
    "starting": ("title", "note"),
    "edit_menu": tuple(native_patches.EDIT_ORDER),
    "hostexit": ("message", "ok", "detail"),
    "shelllog": ("title", "detail", "hints"),
    "packagegrants": ("title", "detail_before", "detail_more", "detail_after"),
    "legacy": ("buttons", "message", "detail"),
    "tray": ("open", "closeToTray", "quit", "idle", "attention", "working", "jobs"),
}
SHELL_HINTS = ("timeout", "exited", "spawn")
PUSH_KEYS = ("approval", "input", "error", "other")


def _keys(path):
    data = common.read_json(path, {})
    return data if isinstance(data, dict) else {}


def _safe_path(rel):
    full = os.path.abspath(os.path.join(paths.ROOT, str(rel)))
    root = os.path.abspath(paths.ROOT)
    return full if full == root or full.startswith(root + os.sep) else None


def validate_profile(code, allow_partial=False):
    errors = []
    warnings = []
    profile = paths.load_profile(code)
    if code != "_template" and profile["code"] != code:
        errors.append("code %r не совпадает с именем профиля %r" % (profile["code"], code))
    if not CODE_RE.match(str(profile["code"])):
        errors.append("code не похож на BCP 47: %r" % profile["code"])
    base = profile.get("base") or str(profile["code"]).split("-")[0]
    if base != str(profile["code"]).split("-")[0]:
        errors.append("base %r не совпадает с первым подтегом code %r" % (base, profile["code"]))
    aliases = profile.get("aliases") or []
    if not isinstance(aliases, list) or any(not isinstance(x, str) or not CODE_RE.match(x) for x in aliases):
        errors.append("aliases должен быть списком BCP 47-кодов")
    if not profile.get("display"):
        errors.append("display пуст")
    if not GLOBAL_RE.match(str(profile.get("global", ""))):
        errors.append("global должен выглядеть как __RU_RU")
    if not IDENT_RE.match(str(profile.get("native", {}).get("uilang", {}).get("checker", ""))):
        errors.append("native.uilang.checker должен быть JS-идентификатором")

    dict_path = _safe_path(profile.get("dictionary", ""))
    if not dict_path or not os.path.isfile(dict_path):
        errors.append("dictionary не найден: %r" % profile.get("dictionary"))
        dictionary = {}
    else:
        dictionary = _keys(dict_path)
    template = _keys(TEMPLATE)
    missing = set(template) - set(dictionary)
    extra = set(dictionary) - set(template)
    if missing:
        message = "в словаре нет %d ключей" % len(missing)
        (warnings if allow_partial else errors).append(message)
    if extra:
        errors.append("в словаре %d лишних ключей" % len(extra))
    for key, value in dictionary.items():
        if not isinstance(value, str) or not value.strip():
            (warnings if allow_partial else errors).append("пустой перевод: %s" % common.short(key, 60))
            continue
        problems = common.placeholder_problems(key, value)
        if problems:
            errors.append("плейсхолдеры %s: %s" % (common.short(key, 40), "; ".join(problems)))
        if common.looks_untranslated(key, value):
            warnings.append("похоже на непереведённую строку: %s" % common.short(key, 50))
    overrides_path = profile.get("overrides")
    if overrides_path:
        full = _safe_path(overrides_path)
        if full and os.path.isfile(full):
            overrides = _keys(full)
            for key, value in overrides.items():
                if not isinstance(value, str) or not value.strip():
                    errors.append("пустой override: %s" % common.short(key, 60))
                elif key in template:
                    problems = common.placeholder_problems(key, value)
                    if problems:
                        errors.append("override %s: %s" % (common.short(key, 40), "; ".join(problems)))

    native = profile.get("native", {})
    for section, keys in NATIVE_SECTIONS.items():
        obj = native.get(section, {})
        if not isinstance(obj, dict):
            errors.append("native.%s должен быть объектом" % section)
            continue
        for key in keys:
            if key not in obj:
                errors.append("native.%s.%s отсутствует" % (section, key))
    hints = native.get("shelllog", {}).get("hints", {})
    for key in SHELL_HINTS:
        if not isinstance(hints.get(key), str) or not hints.get(key).strip():
            errors.append("native.shelllog.hints.%s пуст" % key)
    legacy = native.get("legacy", {})
    if not isinstance(legacy.get("buttons"), list) or len(legacy.get("buttons", [])) != 2:
        errors.append("native.legacy.buttons должен содержать 2 строки")

    push = profile.get("push", {})
    for key in PUSH_KEYS:
        pair = push.get(key)
        if not isinstance(pair, list) or len(pair) != 2 or any(not isinstance(x, str) or not x for x in pair):
            errors.append("push.%s должен содержать 2 непустые строки" % key)

    patches = profile.get("native_patches")
    if patches is not None:
        if not isinstance(patches, list) or not patches:
            errors.append("native_patches должен быть непустым списком")
        else:
            for item in patches:
                if not isinstance(item, dict) or not item.get("file") or not isinstance(item.get("reps"), list):
                    errors.append("native_patches: некорректный элемент")
                    continue
                for rep in item["reps"]:
                    if not isinstance(rep, list) or len(rep) != 3 or any(not isinstance(x, str) for x in rep):
                        errors.append("native_patches.%s: ожидается [tag, old, new]" % item["file"])

    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", help="код языка; по умолчанию все реальные профили")
    parser.add_argument("--allow-partial", action="store_true",
                        help="разрешить неполный словарь (для шаблона/черновика)")
    args = parser.parse_args(argv)

    if args.lang:
        codes = [args.lang]
    else:
        codes = [p["code"] for p in paths.list_profiles()]
    failed = False
    for code in codes:
        errors, warnings = validate_profile(code, args.allow_partial)
        common.log("== %s" % code)
        for warning in warnings[:20]:
            common.log("  ! " + warning)
        for error in errors[:40]:
            common.log("  ERROR " + error)
        if errors:
            failed = True
            common.log("  FAIL: %d ошибок" % len(errors))
        else:
            common.log("  OK: ошибок нет, предупреждений %d" % len(warnings))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
