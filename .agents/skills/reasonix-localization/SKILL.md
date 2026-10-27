---
name: reasonix-localization
description: Work with the Reasonix localization repo: BCP 47 language packs, native patches, validation, tests, and PRs.
runAs: inline
---

# Reasonix Localization — operator skill

Use this skill when working in `Reasonix-RU-Localization`. The repo began as a
Russian localization and now hosts BCP 47 language packs; **`ru-RU` is the
reference implementation**, not the only allowed language. It is not a plugin
and not a fork: it patches a user's installed Reasonix Studio files, keeps
backups, and can roll back.

## Read first

1. `README.md` (English default) and `README.ru.md`.
2. `docs/ADDING-A-LANGUAGE.md` — the authoritative BCP 47 language-pack guide.
3. `docs/ARCHITECTURE.md` and `docs/TROUBLESHOOTING.md`.
4. `CONTRIBUTING.md` — PR and verification rules.

If a command here disagrees with the scripts, inspect the script and update the
docs rather than guessing.

## Quick routing

| Task | Workflow |
|---|---|
| Add a new language (`de-DE`, `pt-BR`, `ja-JP`, …) | **A** |
| Fix an existing translation (Russian reference) | **B** |
| Update after a Reasonix release | **C** |
| Submit a pull request | **D** |

## Hard safety rules

- **Never modify the installed Reasonix Studio** unless the user explicitly asks
  to apply. Default to `--dry-run`, a copy, or `work/test/app`.
- **Close Reasonix Studio completely** (including tray) before applying native
  files. `inject.py` refuses to write while it runs; `--allow-running` is only for
  test copies.
- `C:\Program Files\Reasonix Studio` needs Administrator rights.
- **Do not edit CSS or layout.** Use dictionary values and
  `locale/<code>.overrides.json` for shorter labels.
- Preserve every `{placeholder}` exactly. Never invent, rename, or remove braces.
- Apply **one locale at a time**. Restore before switching.
- Never commit `work/`, `app.asar`, generated caches, API keys, tokens, session
  data, private code, or personal information.
- Do not redistribute Reasonix source, bundles, or binaries.
- Direct pushes to `main` are blocked. Use a branch + PR.
- `automerge` is a maintainer label. Never label an untrusted or unreviewed PR.

## Repo map

```text
languages/<code>.json       language profile (BCP 47)
locale/<code>.json          Chinese keys -> target-language values
locale/<code>.overrides.json manual corrections
locale/_template.json       Chinese -> English template (5,201 keys)
languages/_template.json    English profile template, code "xx-XX"
translations/               legacy compatibility copies
scripts/inject.py           web + settings + push injector (--lang)
scripts/patch_asar.py       native Electron patcher (--lang)
scripts/build_native_patches.py  profile.native -> native_patches
scripts/translate_api.py    DeepSeek translator (--lang)
scripts/merge_parts.py      merge parts + overrides (--lang)
scripts/validate_language_pack.py  PR/CI pack validator
scripts/check_docs.py       docs links/required files
scripts/verify_web.py       copy-only integration test (--lang)
scripts/menu.py             bilingual menu; pack selector via --lang
LOCALIZE.bat                generic launcher
LOCALIZE-RU.bat             Russian default (ru -> ru-RU)
tests/                      unit and profile tests
```

The reference locale is **`ru-RU`**. `ru` remains an alias, so old Russian
commands and `LOCALIZE-RU.bat` keep working. The generic template is **`xx-XX`**;
new languages are first-class, not forks of the Russian pack.

## Profile model

`languages/<code>.json` fields:

| Field | Meaning |
|---|---|
| `code` | BCP 47 locale, e.g. `de-DE`, `pt-BR`, `zh-Hans` |
| `base` | primary subtag used for `navigator.language`/native/push detection |
| `aliases` | accepted legacy/short codes, e.g. `["de"]` |
| `display` | label in Settings → Language |
| `global` | JS dictionary name, `__DE_DE` (identifier; hyphens -> underscores) |
| `dictionary` | `locale/<code>.json` |
| `overrides` | `locale/<code>.overrides.json` |
| `target_language` | translator target, e.g. `German` |
| `glossary` | terminology for the translator |
| `native` | simple Electron strings (startup, menus, dialogs, tray) |
| `push` | four pairs of PWA notification texts |
| `native_patches` | generated JS replacements from `native` |

`locale/<code>.json` is a flat object: **Chinese source key -> translated value**.
The template has 5,201 keys; 45 have no English reference and must be translated
from Chinese.

## Workflow A — add a new language

Example: German `de-DE`.

```bat
gh repo fork itsbuyru-bit/Reasonix-RU-Localization --clone
cd Reasonix-RU-Localization
git switch -c translation/de-DE

copy languages\_template.json languages\de-DE.json
copy locale\_template.json locale\de-DE.json
copy locale\_template.overrides.json locale\de-DE.overrides.json
```

Edit `languages\de-DE.json`:

```json
"code": "de-DE",
"base": "de",
"aliases": ["de"],
"display": "Deutsch",
"global": "__DE_DE",
"dictionary": "locale/de-DE.json",
"overrides": "locale/de-DE.overrides.json",
"target_language": "German"
```

Fill `glossary`, `native` and `push`; then:

```bat
py scripts\build_native_patches.py --lang de-DE
```

Translate the **values** in `locale\de-DE.json`; keep keys and placeholders.
Optional machine pass:

```bat
py scripts\extract_source.py
py scripts\translate_api.py --lang de-DE
py scripts\merge_parts.py --lang de-DE --write
```

Validate and verify:

```bat
py scripts\validate_language_pack.py --lang de-DE
py scripts\check_docs.py
python -m unittest discover -s tests
py scripts\verify_web.py --lang de-DE
py scripts\patch_asar.py --lang de-DE --dry-run
```

Apply only when the user asks:

```bat
py scripts\inject.py --lang de-DE
py scripts\patch_asar.py --lang de-DE --install
```

Or `LOCALIZE.bat --lang de-DE` / the menu pack selector.

## Workflow B — fix an existing translation (Russian reference)

1. Add the key and corrected value to `locale/ru-RU.overrides.json`.
2. Regenerate the dictionary:

```bat
py scripts\merge_parts.py --lang ru-RU --write
```

3. Validate:

```bat
py scripts\validate_language_pack.py --lang ru-RU
py scripts\check_docs.py
python -m unittest discover -s tests
```

4. Commit and PR with the `translation` label.

Do not hand-edit `locale/ru-RU.json` for a single correction; it is generated
from parts + overrides. `merge_parts.py` preserves existing values, so an
override-only correction does not drop the rest of the dictionary.

## Workflow C — update after a Reasonix release

```bat
py scripts\extract_source.py
py scripts\translate_api.py --lang ru-RU
py scripts\merge_parts.py --lang ru-RU --write
py scripts\verify_web.py --lang ru-RU
py scripts\patch_asar.py --lang ru-RU --dry-run
```

If an anchor count is not exactly one, **stop**. Do not force a patch. Check the
Reasonix version, update the profile/native anchors or `native_patches`, and run
the dry-run again.

## Workflow D — pull request

```bat
git add languages\de-DE.json locale\de-DE.json locale\de-DE.overrides.json
git commit -m "translation: add German (de-DE)"
git push -u origin translation/de-DE
gh pr create --base main --head <your-user>:translation/de-DE ^
  --title "translation: add German (de-DE)" ^
  --body "Adds the BCP 47 de-DE language pack."
```

Add label `translation`. CI must pass `Tests (Windows)` (unit tests + language
pack validator + docs check + JSON). Branch protection requires it. A maintainer
may add `automerge`; GitHub then merges after required checks. Never bypass CI.

## Verification checklist

Before reporting done:

- [ ] `validate_language_pack.py --lang <code>` has **0 errors** (warnings are
      allowed; explain them).
- [ ] `check_docs.py` has 0 errors.
- [ ] `python -m unittest discover -s tests` is green.
- [ ] `verify_web.py --lang <code>` passed on a copy.
- [ ] `patch_asar.py --lang <code> --dry-run` passed (11/11 markers, `node --check`).
- [ ] Placeholders preserved; no empty values; no accidental Chinese in a
      non-Chinese pack.
- [ ] No secrets, `app.asar`, or `work/` in the diff.
- [ ] Report exact commands and results; do not claim a check you did not run.

## Troubleshooting

| Symptom | Cause / action |
|---|---|
| `Языковой профиль не найден` | Wrong `--lang`/file name; `ru` aliases `ru-RU`; `_template` is not a real code |
| `Бандл уже локализован другим языком` | Restore from `work/backup`; apply one locale at a time |
| Anchor count 0 or >1 | Reasonix version changed; stop, inspect, update anchors/profile; do not force |
| Settings shows `u` / `y` | Broken old pair; restore, then reapply with current injector |
| Permission denied / `EPERM` | Close Studio; run as Administrator for `Program Files` |
| Old UI after apply | Quit fully; use menu option 6 (cache reset) |
| `patch_asar` says app.asar is locked | Close all Reasonix processes; retry |
| Push test skipped | Expected for non-`ru` packs; `push-sw.js` is still syntax-checked |
| Native already patched | Idempotent detection logs `(уже)`; use a pristine `app.asar` for a clean rebuild |
| Too-long label (e.g. Russian) | Add a shorter value to `locale/<code>.overrides.json`; do not change CSS |

## What not to do

- Do not add a third-party CSS/layout patch.
- Do not edit installed `app.asar` or bundles without an explicit apply request.
- Do not copy Reasonix source/bundles into the repo or a release.
- Do not delete versioned backups; the first copy is the rollback reference.
- Do not commit API keys or `%APPDATA%\reasonix\.env`.
- Do not merge a translation without CI and human review.
- Do not push directly to `main`; use a PR.
