"""Универсальный нативный патчер: python patch_asar.py --lang <code>.

Старое имя patch_asar_ru.py остаётся совместимой обёрткой.
"""
import sys
import patch_asar_ru


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if "--lang" not in args:
        args = ["--lang", "ru"] + args
    return patch_asar_ru.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
