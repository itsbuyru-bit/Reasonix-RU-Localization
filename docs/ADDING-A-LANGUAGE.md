# Adding another language

The toolchain is language-profile based. A new language is **data, not code**:
you add a profile and a dictionary. The Python scripts stay untouched.

Russian is the reference implementation:

- `languages/ru.json` — profile, native Electron strings, push texts, glossary;
- `translations/ru.json` — 5,201 Chinese keys → Russian values;
- `translations/ru_overrides.json` — optional manual fixes.

## 1. Copy the templates

```bat
copy languages\_template.json languages\de.json
copy translations\_template.json translations\de.json
copy translations\_template_overrides.json translations\de_overrides.json
```

Do not use `_template` directly. It exists only as a starting point and is ignored
by `list_profiles()`.

## 2. Fill the profile

Edit `languages/de.json`:

```json
{
  "code": "de",
  "display": "Deutsch",
  "global": "__DE",
  "dictionary": "translations/de.json",
  "overrides": "translations/de_overrides.json",
  "target_language": "German",
  "glossary": "Reasonix, DeepSeek ... = not translated; session = Sitzung; ...",
  "native": { ... },
  "push": { ... }
}
```

Rules:

- `code` is lowercase and matches the file name (`de.json` → `de`);
- `global` must be unique and start with `__` (`__DE`, `__PL`, …);
- `display` is what appears in **Settings → Language**;
- `dictionary` and `overrides` are relative to the repository root;
- `target_language` is used by the API translator;
- `glossary` is the terminology list for machine translation (can be empty);
- `native` contains the native Electron strings;
- `push` contains the two-line PWA notification texts.

`native` fields:

| Section | What it is |
|---|---|
| `uilang.checker` | JS function name, e.g. `isGerman` |
| `starting` | startup window title/note |
| `edit_menu` | context-menu labels |
| `hostexit` | kernel-exit dialog |
| `shelllog` | startup-error dialog and hints |
| `packagegrants` | “could not open window” dialog |
| `legacy` | old-version dialog |
| `tray` | tray menu and status formats (`{n}` is the count) |

After filling `native`, generate the JS patch blocks:

```bat
py scripts\build_native_patches.py --lang de
```

This writes `native_patches` into `languages/de.json`. You do not edit Python.

## 3. Translate the dictionary

`translations/_template.json` has **5,201 Chinese keys** and English values.
Translate the **values**, keep the keys unchanged.

45 keys have no English reference (the upstream English catalogue does not cover
them). They have empty values in the template; translate those from the Chinese
key itself. Use `translations/ru.json` as a second reference for meaning.

Keep all placeholders exactly as written: `{n}`, `{text}`, `{model}`, etc.

Optional machine translation:

```bat
py scripts\extract_source.py
py scripts\translate_api.py --lang de
py scripts\merge_parts.py --lang de --write
```

`translate_api.py` reads `target_language` and `glossary` from the profile and
stores checkpoints in `work/de_parts/`. Re-running continues where it stopped.
`merge_parts.py` applies `translations/de_overrides.json` and reports missing
keys, placeholders and suspicious strings.

## 4. Verify on a copy

Close Reasonix Studio first. Then:

```bat
py scripts\verify_web.py --lang de
```

This copies the installed frontend, injects the language, checks Settings,
the boot screen, the ESM dictionary and rolls the copy back. The installed app
is not changed.

For the native layer:

```bat
py scripts\patch_asar.py --lang de --dry-run
```

It extracts `app.asar`, applies the profile’s native patches, runs `node --check`
on the eight files and builds `work\asar\app-de.asar`.

The Russian push test is Russian-only; for other languages `verify_web.py`
skips it and the injected `push-sw.js` is still syntax-checked.

## 5. Apply

Quit Reasonix Studio completely, including the tray icon.

```bat
py scripts\inject.py --lang de
py scripts\patch_asar.py --lang de --install
```

Or use the menu:

```bat
LOCALIZE.bat --lang de
```

Then start Studio and choose **Settings → Language → Deutsch**.

`LOCALIZE-RU.bat`, `inject_ru.py` and `patch_asar_ru.py` remain as Russian
defaults for backward compatibility.

## 6. Updating Reasonix

When Reasonix updates:

1. `py scripts\extract_source.py` — refresh `work/source.json`;
2. `py scripts\translate_api.py --lang de` — translate only new keys;
3. `py scripts\merge_parts.py --lang de --write`;
4. `py scripts\verify_web.py --lang de`;
5. `py scripts\patch_asar.py --lang de --dry-run`.

If an anchor no longer matches, the script stops before writing. Update the
profile’s `native` fields and run `build_native_patches.py --lang de` again.

## Important limitations

- Apply **one language at a time**. Restore the original files before switching:
  `py scripts\inject.py --lang <old> --restore` and
  `py scripts\patch_asar.py --lang <old> --restore`.
- PWA notification language is chosen from `navigator.language`; the service
  worker has no access to `localStorage`.
- The native layer is patched locally. No Reasonix source, bundles or binaries
  are redistributed.
- New Reasonix versions may rename minified variables. The web injector detects
  the known layouts (2.47.x and 2.52/2.53); unknown layouts stop with a clear
  error instead of corrupting the bundle.
- The menu UI itself is Russian/English; the selected **language pack** is
  independent from the menu language.

## File map

```
languages/
  ru.json                 real Russian profile
  _template.json          English template, code "xx"
translations/
  ru.json                 Russian dictionary, 5,201 keys
  ru_overrides.json       Russian manual fixes
  _template.json          Chinese keys → English values
  _template_overrides.json empty override file
scripts/
  inject.py               web injector, --lang
  patch_asar.py           native patcher, --lang
  build_native_patches.py native JS blocks from profile.native
  translate_api.py        API translator, --lang
  merge_parts.py          dictionary merger, --lang
  verify_web.py           copy-only verification, --lang
```
