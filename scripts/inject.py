"""Универсальный веб-инъектор: python inject.py --lang <code>.

Старое имя inject_ru.py остаётся обёрткой для совместимости.
"""
import sys
import inject_ru


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if "--lang" not in args:
        args = ["--lang", "ru"] + args
    return inject_ru.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
