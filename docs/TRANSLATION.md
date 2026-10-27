# Translation workflow

This document is for maintainers who need to rebuild, extend, or update the
Russian dictionary.

## Files

| Path | Purpose |
|---|---|
| `translations/ru.json` | Final flat dictionary: Chinese key → Russian text |
| `translations/ru_overrides.json` | Targeted human corrections applied on top |
| `work/source.json` | Extracted source rows: `zh`, `en`, `fr` |
| `work/bundle_dict.json` | Raw `en`/`zh` maps from the installed bundle |
| `work/ru_parts/part_*.json` | Translation checkpoints |
| `work/ru_review.tsv` | Human review table: `zh`, `en`, `ru` |
| `work/report.json` | Missing keys, conflicts, placeholder errors |
| `work/review_terms.json` | Terminology and consistency report |

`work/` is generated and gitignored. `translations/ru.json` and
`translations/ru_overrides.json` are committed.

## Dictionary rules

1. **Never translate the Chinese keys.** They are the lookup keys.
2. **Preserve every `{placeholder}` exactly**: `{n}`, `{name}`, `{model}`, …
   Do not rename, remove, or add braces.
3. **Do not translate product names**: Reasonix, Reasonix Studio, DeepSeek,
   Claude, Gemini, OpenAI, GitHub, VS Code, Windows, macOS, Linux, WeChat Pay,
   Alipay, Douyin, QQ.
4. **Keep technical punctuation** and file names, URLs, and key names.
5. **Use Russian quotes** « »; keep the source's trailing punctuation style.
6. **Buttons and menu items**: infinitive or noun, no trailing period.
7. **Empty source → empty value.**
8. **Partial is safe**: a missing key falls back to Chinese.

## Pipeline

### 1. Extract

```bat
py scripts\extract_source.py
```

- Finds the `i18n-*.js` bundle linked from `index.html`.
- Evaluates the bundle in Node (`extract_bundle.mjs`) and reads `v.en`/`v.zh`
  (2.47.x) or `b.en`/`b.zh` (2.52.x).
- Merges keys with `reference/fr.json` (the French reference fills 16 rows
  that have no English reference in the build).
- Writes `work/source.json` with `zh`, `en`, `fr`.

The source catalog is version-specific. Re-run this after every Reasonix update.

### 2. Translate

```bat
py scripts\translate_api.py --batch 20 --workers 6
```

- Reads `work/source.json`.
- Skips rows already present in `work/ru_parts/`.
- Sends `zh` + English reference to the DeepSeek API.
- Uses a glossary (`kernel` → ядро, `workspace` → рабочая область, `prompt` →
  промпт, `session` → сессия, etc.).
- Validates placeholders; a bad batch is retried, then split, then reported.
- Writes a checkpoint after every batch.

The API key is read from `DEEPSEEK_API_KEY` or
`%APPDATA%\reasonix\.env`. Use `--limit` for a small test:

```bat
py scripts\translate_api.py --limit 20 --batch 5 --workers 1
```

### 3. Merge and validate

```bat
py scripts\merge_parts.py --write
```

Checks:

- missing keys;
- unknown keys;
- conflicting values between parts;
- broken placeholders;
- Chinese text left in a value;
- suspicious leading/trailing spaces, newlines, or length ratios.

`--write` refuses to write if there are missing keys, conflicts, or broken
placeholders. It writes `translations/ru.json` in source order.

### 4. Review terminology

```bat
py scripts\review_terms.py
```

Produces a report of terminology deviations and questionable strings. The
result is advisory; use it to add targeted overrides.

### 5. Overrides

For a one-off correction, add the Chinese key and the Russian text to
`translations/ru_overrides.json`:

```json
{
 "工作台": "Верстак",
 "系统提示": "Системный промпт"
}
```

Then re-run:

```bat
py scripts\merge_parts.py --write
```

`scripts/build_overrides.py` regenerates the current terminology overrides
(workbench, LLM prompt, app sessions, a few short statuses). Do not run it if
you maintain the file by hand; it rewrites the file.

### 6. Verify

```bat
py scripts\verify_web.py --dict translations\ru.json
```

The test copies the installed frontend, restores pristine files from the
versioned backups when available, injects the dictionary into a test app, and
checks the real ESM bundle. It also tests the Settings pair, `index.html`,
`push-sw.js`, the service-worker language selection, and rollback.

## Terminology

The glossary lives in `scripts/translate_api.py`. Core choices:

| English | Russian |
|---|---|
| kernel | ядро |
| host | хост |
| workspace | рабочая область |
| workbench | верстак |
| session | сессия |
| chat | чат |
| conversation | беседа |
| agent / subagent | агент / субагент |
| tool | инструмент |
| trajectory | траектория |
| checkpoint | контрольная точка |
| compaction | сжатие |
| prompt (LLM) | промпт |
| request | запрос |
| permission | разрешение |
| approval | подтверждение |
| sandbox | песочница |
| provider | провайдер |
| marketplace | маркетплейс |
| skill | навык |

`сеанс` is intentionally kept for Windows/SSH sessions; application sessions use
`сессия`. `промпт` is used for LLM prompts; approval and HTTP requests use
`запрос`.

## Adding another language

The pipeline is generic, but a few constants are Russian-specific:

| Where | What |
|---|---|
| `scripts/inject_ru.py` | `LANG`, `GLOBAL`, `DISPLAY`, patch strings |
| `scripts/native_strings.py` | Native Russian text |
| `scripts/translate_api.py` | Target language and glossary |
| `translations/` | New `<code>.json` |
| `README` / menu | Language name and instructions |

A clean implementation would thread a `--lang` parameter through every script.
Until then, fork the repository and adapt these constants.

## Cost and keys

Only new strings are sent to the API after an update. The full 2.47.1 run used
about 422k input and 1.05M output tokens on `deepseek-v4-pro`; the 2.52.0 update
translated 231 new strings (5,188 total), and 2.53.1 added 13 more (5,201 total).
A small update usually costs a few cents. Never commit the key or request logs.

## Quality checks before a release

```bat
py -m unittest discover -s tests
py scripts\merge_parts.py
py scripts\verify_web.py --dict translations\ru.json
py scripts\patch_asar_ru.py --dry-run
```

Review `work/ru_review.tsv` for new or changed strings, and keep
`translations/ru_overrides.json` free of placeholder errors.
