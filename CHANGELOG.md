# Changelog

All notable changes are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[Semantic Versioning](https://semver.org/).

## [1.2.3] — 2026-10-22

### Fixed

- Installations under `C:\Program Files` no longer fail with a raw
  `PermissionError` traceback. The patcher now checks write access before
  changing anything and prints a clear instruction to run `LOCALIZE-RU.bat` as
  administrator.
- The menu warns when Reasonix Studio is installed in a protected folder.
- No application files are written when the permission check fails.

---

## [1.2.2] — 2026-10-21

### Fixed

- More compact labels for narrow settings controls:
  - sidebar sections: `Модели`, `Службы`, `Инструменты`, `Сообщения`;
  - connection test button: `Тест` instead of `Проверить подключение`;
  - inherited model limits show only the value: `{n}`, `{levels}`, `Авто`,
    `Не задано`, `Из настроек` instead of the `Наследует…` prefix.
- `translations/ru_overrides.json` now contains 45 targeted corrections.

No CSS or layout files are modified; the fix is in the Russian dictionary.

---

## [1.2.1] — 2026-10-21

### Fixed

- Compact Russian labels for narrow controls:
  - project filters: `Все`, `В работе`, `Закреп.`, `Архив` instead of
    `Все`, `Выполняется`, `Закреплено`, `Архивировано`;
  - cache-hit price field: `Из кэша` instead of `Попадание в кэш`.
- `translations/ru_overrides.json` now contains 34 targeted corrections.

No CSS or layout files are modified by this release; the fix is purely in the
Russian dictionary and is safe for Reasonix Studio 2.47.x.

---

## [1.2.0] — 2026-10-21

Internationalization and GitHub packaging.

### Added

- **English README** (`README.md`, the GitHub default) with a language link to
  the Russian README (`README.ru.md`).
- **Bilingual menu**: Russian is the default, English is selected at startup or
  with `--en`; `--ru` skips the prompt.
- **English launcher name**: `LOCALIZE-RU.bat` (replaces the Cyrillic file
  name).
- GitHub project files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
  `SUPPORT.md`, issue templates, pull request template, CODEOWNERS, and a
  Windows CI workflow.
- Maintainer documentation: `docs/ARCHITECTURE.md`,
  `docs/TRANSLATION.md`, `docs/TROUBLESHOOTING.md`.
- `.gitattributes`, `.editorconfig`, and an updated `.gitignore`.

### Changed

- The version number is a warning, not a hard gate: a new Reasonix build is
  checked by anchors and stops before writing if they moved.
- `review_terms.py` no longer requires Python 3.9+; the project supports
  Python 3.8+ again.
- CI runs unit tests, Python syntax checks, Node syntax checks, and JSON
  validation on Windows.

### Fixed

- The language selector inserts the pair as **one** array element
  `` [`ru`,`Русский`] ``. An already broken `Settings` file is repaired
  automatically. Earlier versions produced separate `ru` and `Русский` entries,
  shown as “u” and “y”.
- `verify_web.py` restores pristine files from versioned backups and uses a
  separate test backup directory, so it works on an already patched install and
  cannot overwrite real backups.

---

## [1.1.1] — 2026-10-21

### Fixed

- **Language selector array**: the pair is inserted as one element
  `` [`ru`,`Русский`] ``; the broken `` ,`ru`,`Русский`] `` form is repaired in
  place.
- **Integration test isolation**: `verify_web.py` uses a test-only backup
  directory and restores pristine files from `work/backup/<version>/`.
- **Cache reset**: `scripts/clear_cache.py` and menu option **6** remove only
  Chromium caches when an old Settings bundle persists.

---

## [1.1.0] — 2026-10-21

### Added

- Russian **PWA push notifications** in `push-sw.js`: approvals, model
  questions, errors, and generic events.
- `scripts/verify_push_sw.mjs`: a VM test for `ru`/`en`/`zh`, fallback by
  `navigator.languages`, and the count suffix.
- `inject_ru.py` patches `push-sw.js`, creates a versioned backup, and restores
  it with `--restore`.

### Changed

- A non-2.47 version prints a warning and still checks anchors instead of
  refusing to run.

### Notes

- Push notification language follows the browser/OS locale
  (`navigator.language`); a service worker cannot read `localStorage`.

---

## [1.0.0] — 2026-10-21

First complete Russian localization for **Reasonix Studio 2.47.1**.

### Added

- `translations/ru.json` — a complete Russian dictionary (4,957 strings).
- `scripts/inject_ru.py` — injects the dictionary into `i18n-*.js`, teaches the
  resolver `ru`, updates `<html lang>`, and adds **Русский** to the Settings
  language list.
- `scripts/native_strings.py` + `scripts/patch_asar_ru.py` — native Electron
  strings: startup page, context menu, error dialogs, legacy-install dialog,
  tray menu.
- `scripts/translate_api.py` — DeepSeek translation with a glossary,
  checkpoints, placeholder validation, and retry.
- `scripts/verify_web.py` + `scripts/verify_bundle.mjs` — integration test on a
  copy: `ru`/`en`/`zh`, translation, fallback, placeholders.
- `LOCALIZE-RU.bat` + `scripts/menu.py` — apply / web-only / verify / rollback /
  rebuild / cache-reset menu.
- Versioned backups in `work/backup/<version>/`; the first copy is the rollback
  reference.

### Notes

- Verified on Reasonix Studio **2.47.1**; bundles `i18n-DS26LhWq.js`,
  `Settings-B_4tuZ4i.js`.
- An application update replaces patched files; re-apply the localization.
- The Go backend and CLI are not covered; their strings are compiled into the
  binary.
