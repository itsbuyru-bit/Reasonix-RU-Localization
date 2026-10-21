"""Ставит @electron/asar в work/tools (нужен только для app.asar)."""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths

VERSION = "4.3.1"


def main():
    paths.ensure_work()
    if os.path.isfile(paths.ASAR_JS):
        common.log("@electron/asar уже установлен: %s" % paths.ASAR_JS)
        return

    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        raise SystemExit("npm не найден. Установите Node.js или пропустите нативную часть.")

    package_json = os.path.join(paths.ASAR_TOOLS, "package.json")
    if not os.path.isfile(package_json):
        with open(package_json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(
                {"name": "reasonix-ru-tools", "private": True, "version": "1.0.0"},
                f,
                ensure_ascii=False,
                indent=1,
            )
            f.write("\n")

    common.log("Устанавливаю @electron/asar@%s в %s" % (VERSION, paths.ASAR_TOOLS))
    command = [npm, "install", "@electron/asar@%s" % VERSION, "--no-audit", "--no-fund"]
    result = subprocess.run(
        command,
        cwd=paths.ASAR_TOOLS,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        # На Windows npm — это .cmd, иногда его нужно запускать через cmd.exe.
        result = subprocess.run(
            " ".join('"%s"' % part for part in command),
            cwd=paths.ASAR_TOOLS,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
        )
    if result.stdout.strip():
        common.log(result.stdout.strip())
    if result.stderr.strip():
        common.log(result.stderr.strip())
    if not os.path.isfile(paths.ASAR_JS):
        raise SystemExit("Не удалось установить @electron/asar.")
    common.log("Готово: %s" % paths.ASAR_JS)


if __name__ == "__main__":
    main()
