# Architecture

This document explains what the toolchain changes, why it is safe, and where to
look when a new Reasonix Studio release moves something.

## Overview

```text
Reasonix Studio installation
├── resources/app.asar                  ← native Electron shell
│   └── src/*.js                        ← startup, menus, dialogs, tray
└── resources/frontend-next/dist        ← web interface (served locally)
    ├── index.html                      ← boot language
    ├── push-sw.js                      ← PWA notifications
    └── assets/
        ├── i18n-*.js                   ← translation dictionary
        └── Settings-*.js               ← language selector

              extract → translate → merge → inject → verify
```

No Reasonix source is rebuilt or redistributed. The scripts read the installed
files, patch copies, validate them, and write them back with backups.

## Web interface

### Dictionary anatomy

The minified `i18n-*.js` bundle contains a dictionary similar to:

```js
var v = { zh: {}, en: { ... } };
```

The **key** is the Chinese source string. The **value** is the translation.
Chinese itself is the fallback: a missing key renders the key. English is a
separate map.

The bundle also contains the current language variable (`y` in 2.47.1), the
active dictionary (`b`), the localStorage key (`x = "rx-lang"`), and helpers:

- `S()` initializes the language and sets `document.documentElement.lang`;
- `C()` resolves a language code (`zh`/`en` only originally);
- `w()` detects the machine language;
- `D()` adopts a language and reloads;
- `O()` translates a key, substituting `{placeholders}`.

### Injected changes

`scripts/inject_ru.py` applies these replacements, each asserted to match once:

| Tag | Effect |
|---|---|
| `R1_translate` | `O()` consults `globalThis.__RU` when the language is `ru` |
| `R2_resolve` | `C()` accepts `ru` |
| `R3_lang` | `<html lang>` becomes `ru` |
| `R4_adopt` | An explicit `ru` choice is not overwritten by auto-detection |
| `R5_machine` | A Russian machine locale resolves to `ru` |
| `R6_dictionary` | Appends `globalThis.__RU = {...}; v.ru = globalThis.__RU` |
| `R7_settings` | Adds `` [`ru`,`Русский`] `` to the Settings language array |
| `R8_index` | Sets the boot page language to `ru` |
| `P1_ru_text` | Adds Russian notification texts to `push-sw.js` |
| `P2_language` | Adds `pickLanguage()` for `zh`/`ru`/`en` |

The Settings array must contain the pair as **one element**:

```js
[[``,`跟随系统`],[`zh`,`中文`],[`en`,`英文`],[`ru`,`Русский`]]
```

A missing pair of brackets produces separate `ru` and `Русский` entries; the UI
then shows their second characters (`u`, `y`). Version 1.1.1 fixed this and
automatically repairs an already broken array.

### Language flow

1. The window loads the local page.
2. `index.html` chooses the boot language from `rx-lang` (or the machine
   locale).
3. The i18n bundle initializes the current language and dictionary.
4. The Settings selector writes `rx-lang` and reloads the window.
5. `O()` reads the active dictionary (`v.ru`) or falls back to Chinese.

The Settings choice persists in `localStorage` under `rx-lang`.

### Push notifications

`push-sw.js` is a service worker. It cannot read `localStorage`, so it picks the
notification language from `navigator.language` / `navigator.languages`:

```js
function pickLanguage() {
  const tags = [self.navigator.language, ...(self.navigator.languages || [])].filter(Boolean);
  for (const tag of tags) {
    const low = String(tag).toLowerCase();
    if (low.startsWith("zh") || low.startsWith("yue") || low.startsWith("cmn")) return "zh";
    if (low.startsWith("ru")) return "ru";
    if (low.startsWith("en")) return "en";
  }
  return "en";
}
```

The first recognized language wins. A Russian browser/OS locale gets Russian
notifications even if the UI selector is set to English, and vice versa. This is
a deliberate limitation of the service-worker environment.

## Native shell

`resources/app.asar` is extracted with `@electron/asar`, patched in a working
copy, syntax-checked with `node --check`, repacked, extracted again, and checked
by markers. Only then can it be installed.

| File | Responsibility |
|---|---|
| `uilang.js` | Accepts `ru`, detects a Russian machine locale |
| `starting.js` | Boot splash title and note |
| `editmenu.js` | Edit/context menu labels |
| `hostexit.js` | Unexpected kernel exit dialog |
| `shelllog.js` | Startup failure hints and dialog |
| `packagegrants.js` | Window could not open dialog |
| `main.js` | Legacy-install cleanup dialog |
| `tray.js` | Tray labels and status line |

`starting.js` and `shelllog.js` choose a language from the locale string;
`tray.js` builds Russian labels from the fold counters supplied by the kernel.

## Backups and rollback

```text
work/backup/<version>/
├── i18n__i18n-*.js
├── settings__Settings-*.js
├── index__index.html
├── push__push-sw.js
└── app.asar
```

- A backup is written **before** the first change to a file.
- The first backup is the rollback reference; later applies do not overwrite it.
- The version is part of the path, so a backup from one Reasonix build is never
  used to restore another build.
- `inject_ru.py --restore` maps `index.html` and `push-sw.js` back to `dist`,
  and the hashed bundles back to `assets`.
- `patch_asar_ru.py --restore` restores the latest `app.asar` backup for the
  current version.

## Version and anchors

The scripts target Reasonix Studio 2.47.x. A different version is **not**
rejected by number. Instead:

1. the script prints a warning;
2. it verifies every anchor;
3. it stops before writing if any anchor is missing or ambiguous.

This keeps a new release usable when the anchors still match, while preventing a
silent partial patch when they do not.

## Safety invariants

- No anchor may match zero or more than one time.
- No file is written before all of its anchors match.
- JavaScript is syntax-checked before installation.
- The rebuilt `app.asar` is verified by extracting it again.
- The installed application is never touched by `verify_web.py`; it works on a
  copy in `work/test/app`.
- The test suite uses a separate backup directory, so it cannot overwrite the
  user's real backups.
