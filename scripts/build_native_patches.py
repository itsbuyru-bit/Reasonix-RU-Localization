"""Собирает native_patches для языка из простых полей `native` в профиле.

Пример:
  py scripts/build_native_patches.py --lang de
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import native_patches
import paths


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True, help="код языка из languages/<code>.json")
    args = parser.parse_args(argv)

    path = paths.profile_path(args.lang)
    profile = paths.load_profile(args.lang)
    profile["native_patches"] = native_patches.build(profile)
    common.write_json(path, profile, indent=1)
    common.log("Собрано native_patches: %s" % path)
    common.log("Проверьте строки в native_patches перед установкой.")


if __name__ == "__main__":
    main()
