# Adding another language (BCP 47)

The toolchain is language-profile based. A new language is **data, not code**:
a profile, a dictionary and translated native/push strings. The Python scripts
stay untouched.

Canonical files use **BCP 47** locale identifiers with a region or script
subtag:

| File | Language |
|---|---|
| `languages/ru-RU.json` + `locale/ru-RU.json` | Русский |
| `languages/_template.json` + `locale/_template.json` | template `xx-XX` |

`ru` remains an alias for `ru-RU` for backward compatibility. `--lang ru` and
`LOCALIZE-RU.bat` keep working.

## BCP 47 fields

- `code` — full locale stored in `rx-lang`, shown in **Settings → Language** and
  written to `<html lang>`: `ru-RU`, `de-DE`, `pt-BR`, `zh-Hans`.
- `base` — primary language subtag used to match `navigator.language` and the
  native/push detection: `ru`, `de`, `pt`, `zh`.
- `aliases` — legacy/short codes accepted on input, e.g. `["ru"]` for `ru-RU`.
- `global` — unique JS dictionary name. It must be a valid identifier:
  `__RU_RU`, `__DE_DE`, `__PT_BR` (hyphens become underscores).
- `dictionary` — canonical `locale/<code>.json`.
- `overrides` — `locale/<code>.overrides.json`.

The injector stores `code` in Settings/`rx-lang`, but matches `base` when the
operating system reports `ru`, `ru-RU`, `ru-BY`, etc. For non-identifier codes
the bundle gets `b["ru-RU"]`, not an invalid `b.ru-RU`.

## 1. Copy the templates

```bat
copy languages\_template.json languages\de-DE.json
copy locale\_template.json locale\de-DE.json
copy locale\_template.overrides.json locale\de-DE.overrides.json
```

Do not use `_template` directly. It is ignored by `list_profiles()`.

## 2. Fill the profile

Edit `languages/de-DE.json`:

```json
{
  "code": "de-DE",
  "base": "de",
  "aliases": ["de"],
  "display": "Deutsch",
  "global": "__DE_DE",
  "dictionary": "locale/de-DE.json",
  "overrides": "locale/de-DE.overrides.json",
  "target_language": "German",
  "glossary": "Reasonix, DeepSeek ... = not translated; session = Sitzung; ...",
  "native": { ... },
  "push": { ... }
}
```

Rules:

- `code` is the BCP 47 file name without `.json`;
- `base` is the primary subtag (`de` for `de-DE`, `pt` for `pt-BR`);
- `aliases` may include short/legacy codes (`de`, `pt`);
- `global` must start with `__` and be unique;
- `display` is what appears in Settings;
- `dictionary` and `overrides` are relative to the repository root;
- `target_language` is used by the API translator;
- `glossary` is the terminology list for machine translation;
- `native` contains native Electron strings;
- `push` contains the two-line PWA notification texts.

`native` sections:

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
py scripts\build_native_patches.py --lang de-DE
```

This writes `native_patches` into `languages/de-DE.json`; you do not edit Python.

## 3. Translate the dictionary

`locale/_template.json` has **5,201 Chinese keys** and English values.
Translate the **values**, keep the keys unchanged.

45 keys have no English reference; they have empty values. Translate those from
the Chinese key itself. Use `locale/ru-RU.json` as a second reference.

Keep placeholders exactly: `{n}`, `{text}`, `{model}`, etc.

Optional machine translation:

```bat
py scripts\extract_source.py
py scripts\translate_api.py --lang de-DE
py scripts\merge_parts.py --lang de-DE --write
```

`translate_api.py` reads `target_language` and `glossary` from the profile and
stores checkpoints in `work/de-DE_parts/`. Re-running continues where it stopped.
`merge_parts.py` applies `locale/de-DE.overrides.json` and reports missing keys,
placeholders and suspicious strings.

## 4. Verify on a copy

Close Reasonix Studio first. Then:

```bat
py scripts\verify_web.py --lang de-DE
```

This copies the installed frontend, injects the locale, checks Settings, the boot
screen, the ESM dictionary and rolls the copy back. The installed app is not
changed.

For the native layer:

```bat
py scripts\patch_asar.py --lang de-DE --dry-run
```

It extracts `app.asar`, applies the profile’s native patches, runs `node --check`
on the eight files and builds `work\asar\app-de-DE.asar`.

The Russian push test is Russian-only; for other locales `verify_web.py` skips
it and the injected `push-sw.js` is still syntax-checked.

## 5. Apply

Quit Reasonix Studio completely, including the tray icon.

```bat
py scripts\inject.py --lang de-DE
py scripts\patch_asar.py --lang de-DE --install
```

Or use the menu:

```bat
LOCALIZE.bat --lang de-DE
```

Then start Studio and choose **Settings → Language → Deutsch**.

`LOCALIZE-RU.bat`, `inject_ru.py` and `patch_asar_ru.py` remain Russian defaults
(`ru` aliases to `ru-RU`) for backward compatibility.

## 6. Updating Reasonix

When Reasonix updates:

1. `py scripts\extract_source.py` — refresh `work/source.json`;
2. `py scripts\translate_api.py --lang de-DE` — translate only new keys;
3. `py scripts\merge_parts.py --lang de-DE --write`;
4. `py scripts\verify_web.py --lang de-DE`;
5. `py scripts\patch_asar.py --lang de-DE --dry-run`.

If an anchor no longer matches, the script stops before writing. Update the
profile’s `native` fields and run `build_native_patches.py --lang de-DE` again.

## Important limitations

- Apply **one locale at a time**. Restore before switching:
  `py scripts\inject.py --lang <old> --restore` and
  `py scripts\patch_asar.py --lang <old> --restore`.
- PWA notification language is chosen from `navigator.language`; the service
  worker has no access to `localStorage`.
- The native layer is patched locally. No Reasonix source, bundles or binaries
  are redistributed.
- New Reasonix versions may rename minified variables. The web injector detects
  the known layouts (2.47.x and 2.52/2.53); unknown layouts stop with a clear
  error instead of corrupting the bundle.
- The menu UI itself is Russian/English; the selected language pack is
  independent from the menu language.
- `en` and `zh` are built into Reasonix and are not patched by this tool.
- `translations/ru.json` and `translations/_template.json` remain as legacy
  copies; new profiles use `locale/`.

## File map

```
languages/
  ru-RU.json              real Russian profile
  _template.json          English template, code "xx-XX"
locale/
  ru-RU.json              Russian dictionary, 5,201 keys
  ru-RU.overrides.json    Russian manual fixes
  _template.json          Chinese keys → English values
  _template.overrides.json
translations/
  ru.json                 legacy copy of locale/ru-RU.json
  _template.json          legacy copy
scripts/
  inject.py               web injector, --lang
  patch_asar.py           native patcher, --lang
  build_native_patches.py native JS blocks from profile.native
  translate_api.py        API translator, --lang
  merge_parts.py          dictionary merger, --lang
  verify_web.py           copy-only verification, --lang
```
