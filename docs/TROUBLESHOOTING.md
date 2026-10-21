# Troubleshooting

## First checks

1. Which Reasonix Studio version is installed? The menu prints it at startup.
   The tested build is **2.47.1**.
2. Did you completely quit Reasonix Studio before applying, including the tray
   icon? `app.asar` is locked while the app runs.
3. Which menu option did you use: **1** (everything) or **2** (web only)?
4. Does the menu print the dictionary path and a count of 4,957 strings?

If you open an issue, include the exact menu/script output and the version.
Remove API keys, tokens, session data, and private code first.

## “Русский” is missing from the language list

- Run `py scripts\inject_ru.py --dry-run` and check that
  `R7_settings` reports `ok`. A missing or non-unique anchor stops the patch.
- Make sure the Settings bundle is the one the app loads. The injector uses the
  newest `Settings-*.js` in `resources/frontend-next/dist/assets`.
- Clear the interface cache (menu option 6) and restart.

## The language list shows “u” and “y”

This is the old bracket bug, fixed in **1.1.1**. The pair was inserted as
`` ,`ru`,`Русский` `` instead of `` ,[`ru`,`Русский`] ``, so the UI treated
`ru` and `Русский` as two entries and displayed their second characters.

Fix:

1. Quit Reasonix Studio completely.
2. Run `LOCALIZE-RU.bat` → **1 — Apply everything** again. Version 1.1.1
   detects the broken array and repairs it in place.
3. If the old list is still visible, run menu option **6 — Clear the interface
   cache**, then start Studio.

Check the installed file if needed:

```bat
py scripts\inject_ru.py --dry-run
```

It should print `пункт «Русский» уже есть` / “the Russian entry is already
present”.

## Russian is selected but the interface is English

- Confirm you selected **Русский**, not **Follow the system**.
- The window reloads after the language change; wait for the reload.
- Clear the cache (option 6) and restart.
- Verify the dictionary is present:

```bat
py scripts\merge_parts.py
```

It should report 4,957 translated strings.

- If the interface is English but the language list contains **Русский**, the
  i18n bundle may not have the `v.ru` registration. Run
  `py scripts\inject_ru.py --dry-run`; `R6_dictionary` and `v.ru` must be
  reported.

## `app.asar` is locked

Reasonix Studio is still running, or a background process holds the file.

1. Quit the app, including the tray icon.
2. Check Task Manager for `Reasonix Studio.exe` and `reasonix-studio-host.exe`.
3. Retry menu option 1 or 4.

The error message names the locked file. Do not delete `app.asar` manually.

## Python is not found

- Install Python 3.8 or newer from python.org and enable “Add Python to PATH”.
- The launcher tries `py` first, then `python`.
- Verify:

```bat
py --version
```

## Node.js is not found

Node.js 18+ is required for `app.asar` and syntax checks. The web-only option
still works without Node, but the native surfaces are skipped.

```bat
node --version
```

`scripts\vendor_asar.py` installs `@electron/asar` into `work/tools` on demand;
the first native run needs network access.

## DeepSeek API key is missing

Only translation/update needs the key. Add it to
`%APPDATA%\reasonix\.env`:

```text
DEEPSEEK_API_KEY=...
```

Never commit the key or paste it into an issue. Without a key the existing
`translations/ru.json` still applies; new strings stay Chinese.

## A new Reasonix version does not accept the patch

The scripts print a warning for a non-2.47 build and then verify every anchor.
If an anchor moved, they stop before writing and name it.

- Run `py scripts\inject_ru.py --dry-run` and
  `py scripts\patch_asar_ru.py --dry-run`.
- For web anchors, edit `scripts/inject_ru.py`.
- For native anchors, edit `scripts/native_strings.py`.
- Do not disable the “exactly once” check.

If extraction fails because the bundle shape changed, open an issue with the
version and the error.

## Rollback

1. Quit Reasonix Studio completely.
2. Run `LOCALIZE-RU.bat` → **4 — Roll back changes**.
3. Start Studio.

Web files come from `work/backup/<version>/`; `app.asar` comes from its
versioned backup. The first backup is the original and is not overwritten by
later applies.

If the backup folder for the current version is missing, the scripts report it;
do not guess or restore a backup from another version.

## The hosted Web Studio is not translated

`reasonix.io/remote` is served by Reasonix, not by your installation. The patch
only affects your local installation. Local browser/PWA access that serves
`resources/frontend-next/dist` from your machine is translated.

## Push notifications are in the wrong language

The service worker cannot read the in-app language. It uses
`navigator.language` / `navigator.languages`. Set the browser/OS locale to
Russian, or accept English/Chinese notifications. The in-app selector does not
affect push notifications.

## Text overlaps or is clipped in narrow controls

Some controls are sized for short English labels. The project filter bar is a
10 px segmented control; the cache-hit price is a narrow input. Version
**1.2.2** uses compact Russian labels:

- filters: `Все`, `В работе`, `Закреп.`, `Архив`;
- cache-hit price: `Из кэша`;
- Settings sidebar: `Модели`, `Службы`, `Инструменты`, `Сообщения`;
- connection test button: `Тест`;
- inherited model limits: only the value (`1,0M`, `Авто`, `Из настроек`).

If another control still overflows:

1. add an even shorter value to `translations/ru_overrides.json`;
2. run `py scripts\merge_parts.py --write`;
3. re-apply the localization (menu option 1 or 2) and clear the interface cache
   (option 6).

The app's **Settings → Appearance → Interface size** scales all text, not only
the overflowing control. A targeted CSS patch is possible but tied to the build;
open an issue with a screenshot and the affected control.

## Some strings stay Chinese

A missing key falls back to Chinese by design. The included dictionary is
complete for 2.47.1. After updating Reasonix, run menu option **5** to translate
the new strings, then option **1** to apply.

## Antivirus or SmartScreen

The scripts are plain Python and Node; they do not download executables except
`@electron/asar` from npm. If SmartScreen blocks the `.bat`, allow it or run the
commands manually from a terminal.

## Collecting diagnostics safely

Useful:

- Reasonix Studio version;
- Windows version;
- menu option used;
- exact output of `py scripts\inject_ru.py --dry-run`;
- exact output of `py scripts\patch_asar_ru.py --dry-run`;
- a screenshot of the affected screen.

Do **not** include:

- `%APPDATA%\reasonix\.env`;
- provider keys or tokens;
- session content, private code, or personal data;
- the whole `app.asar` or patched bundles.

## Still stuck

Open a bug report:

https://github.com/itsbuyru-bit/Reasonix-RU-Localization/issues/new?template=bug_report.yml

For a wrong translation, use the translation template instead. For a security
problem, use GitHub Security Advisories, not a public issue.
