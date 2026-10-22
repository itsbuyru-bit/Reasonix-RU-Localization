# Reasonix Studio — Russian Localization

**English** | [Русский](README.ru.md)

[![CI](https://github.com/itsbuyru-bit/Reasonix-RU-Localization/actions/workflows/ci.yml/badge.svg)](https://github.com/itsbuyru-bit/Reasonix-RU-Localization/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D4.svg)](#requirements)
[![Reasonix Studio: 2.47.x](https://img.shields.io/badge/Reasonix%20Studio-2.47.x-6f42c1.svg)](#supported-version)

An unofficial Russian localization for **Reasonix Studio 2.47.x**. It adds
**Русский** to the in-app language selector, translates the Electron native
surfaces, and translates the PWA push notifications.

The application is **not rebuilt**. The toolchain edits the user's own
installation, keeps versioned backups, and can roll every change back.

> **Unofficial.** This project is not affiliated with, endorsed by, or
> sponsored by the Reasonix Studio / DeepSeek-Reasonix project or its
> maintainers. See [Non-affiliation](#non-affiliation).

---

## Table of contents

- [What this project does](#what-this-project-does)
- [Features](#features)
- [Supported version](#supported-version)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Menu reference](#menu-reference)
- [How it works](#how-it-works)
- [Manual commands](#manual-commands)
- [Updating after a Reasonix release](#updating-after-a-reasonix-release)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Project structure](#project-structure)
- [Translation data and overrides](#translation-data-and-overrides)
- [Testing](#testing)
- [Contributing](#contributing)
- [Security](#security)
- [License and credits](#license-and-credits)
- [Non-affiliation](#non-affiliation)

---

## What this project does

Reasonix Studio ships its interface in Chinese and English. This project adds a
third language to the same installation:

| Surface | Translated? | How |
|---|---|---|
| Desktop window (Electron web UI) | ✅ | Dictionary injected into the `i18n-*.js` bundle |
| Settings → Language selector | ✅ | `` [`ru`,`Русский`] `` added to the `Settings-*.js` bundle |
| Startup splash language | ✅ | `index.html` patch |
| Native Electron surfaces | ✅ | `app.asar`: startup page, context menu, error dialogs, tray |
| PWA push notifications | ✅ | `push-sw.js` |
| Local web/PWA access from this installation | ✅ | It serves the same patched `frontend-next/dist` files |
| Hosted Web Studio at `reasonix.io/remote` | ❌ | Served by the vendor, not by your installation |
| Go backend / CLI | ❌ | Its strings are compiled into the binary |

The project contains **no Reasonix source code, bundles, or binaries**. It
patches the copy already installed on the machine and stores dated backups.

---

## Features

- **4,957 translated interface strings** — complete dictionary, no blanks.
- **Language selector integration** — choose **Русский** next to 中文 and
  English; the choice persists.
- **Native shell translation** — startup page, right-click menu, error
  dialogs, legacy-install dialog, tray menu.
- **PWA push notifications** — Russian titles and bodies for approvals,
  questions, errors, and generic events.
- **Safe patching** — every anchor must match exactly once; a mismatch stops
  the script before anything is written.
- **Versioned backups** — the first copy of each file is kept as the rollback
  reference and is never overwritten by later runs.
- **One-command rollback** — menu option 4.
- **Reproducible translation pipeline** — extract → translate → validate →
  inject → verify, with checkpoints and overrides.
- **Bilingual menu** — Russian by default, English selectable at startup or
  with `--en`.
- **CI** — unit tests, JSON validation, and Node syntax checks on every push.

---

## Supported version

| Component | Value |
|---|---|
| Reasonix Studio | **2.47.x** — tested on **2.47.1** |
| Web bundles | `i18n-DS26LhWq.js`, `Settings-B_4tuZ4i.js` |
| PWA worker | `push-sw.js` |
| Native bundle | `resources/app.asar` |

The version is not a hard gate. On a different 2.47+ build the scripts print a
warning and still verify every anchor; if an anchor moved, they stop before
writing and report which one. Update the anchors in
`scripts/inject_ru.py` (web) or `scripts/native_strings.py` (native) when that
happens.

An application update replaces the patched files, so the localization must be
applied again after every update. See
[Updating after a Reasonix release](#updating-after-a-reasonix-release).

---

## Requirements

| Need | Why |
|---|---|
| **Windows 10/11** | The scripts use Windows paths and `tasklist`. |
| **Reasonix Studio 2.47.x** | The tool patches your own installation. |
| **Python 3.8+** | All scripts are standard-library Python. |
| **Node.js 18+** | Rebuilding `app.asar` and syntax-checking bundles. |
| **DeepSeek API key** | Only for re-translating new strings after an update. The ready dictionary is included. |

No compiler and no build step are required. The optional DeepSeek key is read
from `%APPDATA%\reasonix\.env` (variable `DEEPSEEK_API_KEY`); it is never
committed to this repository.

---

## Quick start

1. **Quit Reasonix Studio completely** — including the tray icon → **Quit**.
2. Run **`LOCALIZE-RU.bat`** from this folder. If Reasonix Studio is installed
   under `C:\Program Files`, right-click the launcher and choose **Run as
   administrator**.
3. Choose the menu language:
   - `1` — Русский (default, press Enter)
   - `2` — English
4. Choose **1 — Apply everything**.
5. Start Reasonix Studio.
6. Open **Settings → Language → Русский**.

The interface reloads after the language change. If **Русский** is not in the
list, or the old list still appears, see
[Troubleshooting](#troubleshooting).

### Web-only installation

If you do not want to touch `app.asar`:

1. Run `LOCALIZE-RU.bat`.
2. Choose **2 — Web interface only**.
3. Restart Reasonix Studio (or reload the window) and select **Русский**.

This works even while Reasonix Studio is running; the changes apply after the
window reloads.

### English menu shortcut

```bat
LOCALIZE-RU.bat --en
```

Use `--ru` to skip the language prompt and open the Russian menu directly.

---

## Menu reference

| Option | Action |
|---|---|
| **1** | Apply everything: web interface + native `app.asar` |
| **2** | Apply only the web interface |
| **3** | Verify on a copy; nothing in the installation is changed |
| **4** | Roll back web files and `app.asar` from versioned backups |
| **5** | Rebuild the translation from the installed version (after an update) |
| **6** | Clear the Chromium interface cache (if old settings still appear) |
| **7** | Exit |

Option 1 and option 4 require Reasonix Studio to be fully closed. Option 2 can
run while the app is open, but a restart is needed to see the result.

---

## How it works

### Web interface

Reasonix Studio is an Electron application whose window loads a local web page.
The translation dictionary lives in the minified `i18n-*.js` bundle:

```js
var v = { zh: {}, en: { ... } };
```

The **key** is the Chinese source text; the **value** is the translation. The
injector:

1. finds the `i18n-*.js` bundle that `index.html` actually loads;
2. appends `globalThis.__RU = { ... }` and `v.ru = globalThis.__RU`;
3. teaches the translation function `O()` to use `__RU` when the current
   language is `ru`;
4. allows `ru` in the language resolver and in `<html lang>`;
5. prevents machine-language auto-detection from overwriting an explicit `ru`
   choice;
6. adds `` [`ru`,`Русский`] `` to the language list in the `Settings-*.js`
   bundle;
7. patches the startup language in `index.html`;
8. translates the PWA notification worker `push-sw.js`.

Every replacement is asserted to match **exactly once**. If an anchor is not
found, the script reports it and does not write the file.

### Native shell

`resources/app.asar` is unpacked, eight files are patched, the syntax is
checked, and the archive is rebuilt:

| File | What it contains |
|---|---|
| `uilang.js` | Accepts `ru` and detects a Russian machine locale |
| `starting.js` | Startup splash title and note |
| `editmenu.js` | Right-click Edit menu labels |
| `hostexit.js` | “Kernel exited unexpectedly” dialog |
| `shelllog.js` | Startup failure hints and dialog |
| `packagegrants.js` | “Could not open its window” dialog |
| `main.js` | Legacy-install cleanup dialog |
| `tray.js` | Tray menu labels and status line |

The rebuilt archive is verified by extracting it again and checking every
marker. Installation is a separate `--install` step with a backup; a failed
anchor match aborts before anything is installed.

### PWA push notifications

`push-sw.js` gets a Russian `TEXT.ru` block and a `pickLanguage()` helper.
Service workers cannot read `localStorage`, so the notification language is
chosen from `navigator.language` / `navigator.languages` (the browser or OS
locale), not from the in-app selector. A Russian browser/OS locale gets Russian
notifications.

### Safety and rollback

- Every file is copied to `work/backup/<version>/` before it is changed.
- The **first** copy of each file is kept as the rollback reference; later
  applies do not overwrite it.
- `--restore` (menu option 4) copies those files back, including `index.html`
  and `push-sw.js` from `dist` (not from `assets`).
- A partial or failed patch never writes silently.

### Caching

The host serves hashed assets under `/assets/*` with a long-lived immutable
cache. If the old Settings bundle is still shown after a repair, menu option
**6** clears only the Chromium caches (`Cache`, `Code Cache`, `GPUCache`, and
similar). Settings, themes, sessions, `localStorage`, and cookies are not
touched.

---

## Manual commands

```bat
py scripts\extract_source.py
py scripts\translate_api.py --batch 20 --workers 6
py scripts\merge_parts.py --write
py scripts\review_terms.py
py scripts\verify_web.py --dict translations\ru.json
py scripts\patch_asar_ru.py --dry-run

py scripts\inject_ru.py
py scripts\patch_asar_ru.py --install

py scripts\inject_ru.py --restore
py scripts\patch_asar_ru.py --restore
py scripts\clear_cache.py
```

`inject_ru.py --dry-run` only checks the web anchors. `patch_asar_ru.py
--dry-run` builds and verifies `work/asar/app-ru.asar` without installing it.

---

## Updating after a Reasonix release

An application update replaces the patched files, so the Russian option
disappears. This is expected.

1. Run `LOCALIZE-RU.bat`.
2. Choose **5 — Rebuild the translation from the installed version**.
3. The script:
   - extracts strings from the new installation;
   - translates **only new strings** (existing parts are reused, so the API is
     used only for what is new);
   - rebuilds and validates the dictionary;
   - verifies the anchors on a copy.
4. If verification passes, choose **1 — Apply everything**.
5. If an anchor moved, the script stops and names it. Update
   `scripts/inject_ru.py` (web) or `scripts/native_strings.py` (native), or
   open an issue with the output.

Existing translations are matched by the Chinese key. If a Chinese key changes,
the string is treated as new and translated again. If only the English
reference changes under the same key, the old Russian value is kept — review
such rows in `work/ru_review.tsv`.

The version number is a warning, not a hard block: on a new build the anchors
decide whether the patch can be applied.

---

## Troubleshooting

### “Русский” is missing, or the list shows “u” and “y”

This was a bug in versions before **1.1.1**: the language pair was inserted
without brackets, so the UI treated `ru` and `Русский` as separate entries and
displayed their second characters. Version 1.1.1 adds the correct pair
`` [`ru`,`Русский`] `` and automatically repairs an already broken
`Settings-*.js`.

If you are upgrading from an older copy:

1. Quit Reasonix Studio completely.
2. Run `LOCALIZE-RU.bat` → **1 — Apply everything** again (this repairs the
   file), or restore from `work/backup/<version>/` and apply again.
3. If the old list is still shown, run menu option **6 — Clear the interface
   cache**, then start Studio.

### The interface is still English after choosing Русский

- Make sure you selected **Русский**, not **Follow the system**.
- The language change reloads the window; wait for it to finish.
- Clear the interface cache (menu option 6) and restart.
- Check that `translations/ru.json` was found: the menu prints its path and
  string count at startup.

### `app.asar` is locked

Reasonix Studio is still running. Quit it completely, including the tray icon,
then retry option 1 or 4. The error message names the locked file.

### Permission denied / the app is in Program Files

If Reasonix Studio is installed under `C:\Program Files`, a normal user cannot
write to `resources\...`. The patcher stops before changing anything and prints
the folder name.

1. Quit Reasonix Studio completely.
2. Right-click `LOCALIZE-RU.bat` and choose **Run as administrator**.
3. Choose option 1 or 2.

The cache reset (option 6) does not need administrator rights. Installing
Reasonix Studio outside `Program Files` also avoids the problem.

### Python or Node is not found

- Python 3.8+ is required. The `.bat` tries `py` first, then `python`.
- Node.js 18+ is required for `app.asar` and syntax checks. The web-only
  option still works without Node, but the native part is skipped.

### DeepSeek API key is missing

Only the translation/update step needs it. Add the key to
`%APPDATA%\reasonix\.env`:

```text
DEEPSEEK_API_KEY=...
```

Do not paste keys into issues or pull requests. If the key is absent, the
existing dictionary still applies; new strings fall back to Chinese.

### I want to undo everything

Quit Reasonix Studio and choose **4 — Roll back changes**. Web files and
`app.asar` are restored from `work/backup/<version>/`. The cache reset is
separate (menu option 6).

### Unsupported version or moved anchors

The scripts print the anchor name and the number of matches. Do not force a
write. Update the anchors, or open an issue with the full output and the
Reasonix Studio version. On a new version, extraction may still work even when
injection needs new anchors.

### Hosted Web Studio is not translated

`reasonix.io/remote` is served by the vendor. The patch applies only to your
local installation. Local browser/PWA access that serves
`resources/frontend-next/dist` from your machine is translated.

### Push notifications are in the wrong language

The service worker cannot read the in-app language. It follows
`navigator.language` / `navigator.languages`; set the browser/OS locale to
Russian, or accept English/Chinese notifications.

### Text overlaps or is clipped in narrow controls

Some controls were sized for short English labels: the project filter bar is a
10 px segmented control, and the cache-hit price is a narrow input. Version
**1.2.2** uses compact labels:

- project filters: `Все`, `В работе`, `Закреп.`, `Архив`;
- cache-hit price: `Из кэша`;
- Settings sidebar: `Модели`, `Службы`, `Инструменты`, `Сообщения`;
- connection test button: `Тест`;
- inherited model limits: the field shows only the value (`1,0M`, `Авто`,
  `Из настроек`) instead of the `Наследует…` prefix.

If another control still overflows:

1. add a shorter value to `translations/ru_overrides.json` and run
   `py scripts\merge_parts.py --write`;
2. re-apply the localization (menu option 1 or 2) and clear the interface cache
   (menu option 6);
3. the app's own **Settings → Appearance → Interface size** scales all text, but
   it affects the whole UI. A CSS patch is possible but tied to the build — open
   an issue with a screenshot.

### Some strings remain Chinese

A missing key falls back to Chinese by design; it never renders blank. The
included dictionary is complete for 2.47.1, but a newer build may add strings.
Run the update procedure (menu option 5) to translate them.

---

## Limitations

- **Windows-oriented.** The logic is portable, but paths and `tasklist` are
  Windows-specific.
- **Anchors are verified on 2.47.x.** A new build is checked by anchors, not by
  the version number; if they moved, the patch stops.
- **Go backend and CLI are not covered.** Their strings are compiled into the
  binary.
- **An app update removes the patch.** Apply it again after updating.
- **The legacy-install dialog** (`main.js`) is translated based on the system
  locale; it is shown very rarely.
- **Push notification language** follows the browser/OS locale, not the in-app
  selector.
- **Hosted Web Studio** is out of scope; only the local installation is patched.
- **Bilingual menu, Russian tool logs:** the menu is English/Russian; low-level
  diagnostic output from the Python tools is currently in Russian.
- **Partial dictionaries are safe:** omitted strings fall back to Chinese.

---

## Project structure

```text
Reasonix-RU-Localization/
├── LOCALIZE-RU.bat              # bilingual menu launcher
├── README.md                    # English (default)
├── README.ru.md                 # Russian
├── LICENSE
├── LICENSE-REASONIX.md
├── THIRD-PARTY.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── SUPPORT.md
├── translations/
│   ├── ru.json                  # 4,957 Russian strings
│   └── ru_overrides.json        # targeted corrections
├── reference/
│   └── fr.json                  # French reference (MIT), for cross-checks
├── scripts/
│   ├── paths.py                 # install detection and paths
│   ├── common.py                # JSON, placeholders, checks
│   ├── extract_source.py        # read the installed bundle
│   ├── extract_bundle.mjs       # evaluate the minified bundle
│   ├── translate_api.py         # DeepSeek translation with checkpoints
│   ├── merge_parts.py           # merge and validate the dictionary
│   ├── review_terms.py          # terminology review report
│   ├── build_overrides.py       # regenerate ru_overrides.json
│   ├── inject_ru.py             # web + push injection
│   ├── native_strings.py        # Russian native strings
│   ├── patch_asar_ru.py         # build/install app.asar
│   ├── vendor_asar.py           # install @electron/asar
│   ├── verify_web.py            # integration test on a copy
│   ├── verify_bundle.mjs        # ESM ru/en/zh test
│   ├── verify_push_sw.mjs       # service-worker VM test
│   ├── clear_cache.py           # safe Chromium cache reset
│   └── menu.py                  # bilingual menu
├── tests/                       # unit tests and dictionary checks
├── docs/                        # architecture, translation, troubleshooting
├── .github/                     # CI, issue templates, PR template
└── work/                        # generated at runtime, not committed
```

---

## Translation data and overrides

`translations/ru.json` is a flat object:

```json
{
  "重命名聊天": "Переименовать чат",
  "聊天标题": "Название чата"
}
```

- **Keys must never be translated.** They are the lookup keys.
- **Keep every `{placeholder}` exactly as written** (`{n}`, `{name}`,
  `{model}`, …).
- **Do not translate product names** such as Reasonix, DeepSeek, WeChat Pay,
  Alipay, GitHub, VS Code.
- Empty source → empty value.

Targeted corrections live in `translations/ru_overrides.json`. They are applied
on top of the machine translation and do not need a new API run:

```json
{
 "工作台": "Верстак",
 "系统提示": "Системный промпт"
}
```

After editing an override, run:

```bat
py scripts\merge_parts.py --write
```

`scripts/build_overrides.py` regenerates the current terminology overrides
(`промпт`/`сессия`, “Верстак”, and a few short status strings). Do not run it
if you maintain the override file by hand; it rewrites the file.

For the full maintainer workflow, see
[docs/TRANSLATION.md](docs/TRANSLATION.md).

---

## Testing

```bat
py -m unittest discover -s tests
py scripts\verify_web.py --dict translations\ru.json
py scripts\patch_asar_ru.py --dry-run
node --check scripts\extract_bundle.mjs
node --check scripts\verify_push_sw.mjs
```

`verify_web.py` copies the frontend and `app.asar` to `work/test/app`,
restores pristine files from `work/backup/<version>/` when available, applies
the dictionary, and verifies:

- `ru` → `en` → `zh` switching through the real ESM bundle;
- the Russian string is returned;
- the English dictionary still works;
- Chinese fallback returns the original key;
- `{placeholder}` substitution;
- the Settings language pair, `index.html`, and `push-sw.js`;
- the service worker for `ru`/`en`/`zh`, fallback and the count suffix;
- rollback to the original files.

The installed application is not modified by the test. CI runs the unit suite,
JSON validation, and Node syntax checks on every push.

---

## Contributing

Issues and pull requests are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md) and the
[translation workflow](docs/TRANSLATION.md). Translation fixes are especially
useful: include the screen, the Chinese/English source, the current Russian
text, and a suggested correction.

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).

---

## Security

Do not paste API keys, session data, private code, or screenshots containing
secrets into issues. Report security problems privately through GitHub Security
Advisories; see [SECURITY.md](SECURITY.md).

---

## License and credits

- This project: **MIT**, © 2026 **itsbuyru-bit**. See [LICENSE](LICENSE).
- The toolchain and anchor approach are derived from
  [Reasonix-Traduction-Fr](https://github.com/xtrem21-source/Reasonix-Traduction-Fr)
  (MIT, © 2026 Reasonix-Traduction-Fr contributors). See
  [THIRD-PARTY.md](THIRD-PARTY.md).
- Reasonix Studio / DeepSeek-Reasonix is MIT, © Reasonix Contributors; the
  license text is kept in [LICENSE-REASONIX.md](LICENSE-REASONIX.md).
- `@electron/asar` is MIT and is installed on demand into `work/tools`.
- The optional translation step uses the DeepSeek API; no keys or request logs
  are included in this repository.

---

## Non-affiliation

This is an independent, unofficial project. It is **not affiliated with,
endorsed by, or sponsored by** the DeepSeek-Reasonix project (Reasonix Studio),
its maintainer, or its contributors.

It contains no Reasonix source code, JavaScript bundles, Go binary, or
`app.asar`. It operates only on the copy installed on the user's machine.
“DeepSeek-Reasonix” and “Reasonix Studio” belong to their respective authors.
