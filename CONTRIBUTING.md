# Contributing

Thank you for improving the Russian localization of Reasonix Studio. This
project is small and practical: every change should be reproducible, reversible,
and safe for the user's installation.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- **Fix a translation.** This is the most useful contribution.
- **Report a bug** in the patcher, the menu, or the update pipeline.
- **Improve documentation** or the troubleshooting guide.
- **Add a new language.** The pipeline is generic; see
  [docs/TRANSLATION.md](docs/TRANSLATION.md).
- **Update anchors** for a newer Reasonix Studio release.

## Reporting bugs

Open a [bug report](https://github.com/itsbuyru-bit/Reasonix-RU-Localization/issues/new?template=bug_report.yml)
and include:

- Reasonix Studio version (for example `2.47.1`);
- Windows version;
- what you did, what you expected, and what happened;
- the exact menu/script output;
- screenshots of the affected screen, if useful.

**Remove API keys, tokens, session data, private code, and personal information**
from logs and screenshots before posting. Do not paste the contents of
`%APPDATA%\reasonix\.env`.

## Fixing a translation

Open a [translation issue](https://github.com/itsbuyru-bit/Reasonix-RU-Localization/issues/new?template=translation.yml)
or edit `translations/ru_overrides.json` directly and open a pull request.
Include:

- the screen where the string appears;
- the Chinese source and/or English reference if you know it;
- the current Russian text;
- the suggested Russian text;
- confirmation that every `{placeholder}` is preserved.

For a one-off correction, add the key to `translations/ru_overrides.json`, then:

```bat
py scripts\merge_parts.py --write
```

Do not edit `translations/ru.json` by hand for a single fix: it is regenerated
from `work/ru_parts/` plus overrides.

## Development setup

```bat
git clone https://github.com/itsbuyru-bit/Reasonix-RU-Localization.git
cd Reasonix-RU-Localization
python -m unittest discover -s tests
```

Requirements: Python 3.8+ and Node.js 18+. There is no build step and no
third-party Python dependency. `@electron/asar` is installed into `work/tools`
on demand by `scripts/vendor_asar.py`.

The integration tests need a local Reasonix Studio installation and a generated
source catalog:

```bat
py scripts\extract_source.py
py scripts\verify_web.py --dict translations\ru.json
py scripts\patch_asar_ru.py --dry-run
```

They copy the application into `work/test/app` and never modify the installed
copy.

## Code conventions

- Python standard library only; no new dependencies without a strong reason.
- UTF-8, LF line endings, 4-space indentation (see `.editorconfig`).
- Keep user-facing messages clear; the menu is bilingual.
- Every patch anchor must match **exactly once**. Never add a “best effort”
  replacement that writes on a partial match.
- Preserve the versioned backup model: the first copy is the rollback
  reference and must not be overwritten.
- Do not commit `work/`, generated dictionaries, API keys, or `app.asar`.
- Do not redistribute Reasonix source code, bundles, or binaries.

## Commit and pull request conventions

Use short, imperative commit messages. [Conventional Commits](https://www.conventionalcommits.org/)
prefixes are welcome:

```text
feat: add Russian push notification texts
fix: insert the language pair as one array element
docs: document the cache reset
test: cover the broken Settings array
```

A pull request should:

- solve one topic;
- include tests or a manual verification note;
- update `README.md` / `README.ru.md` and `CHANGELOG.md` when behavior changes;
- include screenshots for visible UI changes;
- pass `python -m unittest discover -s tests` and the Node syntax checks.

## Updating anchors for a new Reasonix version

The web anchors live in `scripts/inject_ru.py`; the native anchors live in
`scripts/native_strings.py`. Before changing them:

1. run `py scripts\extract_source.py`;
2. run `py scripts\inject_ru.py --dry-run`;
3. run `py scripts\patch_asar_ru.py --dry-run`.

The scripts report the anchor name and the number of matches. Add or update a
test for any new anchor. Do not merge a change that writes on a non-unique
match.

## License of contributions

By submitting a contribution, you agree that it is licensed under the MIT
License of this repository (see `LICENSE`). The French toolkit attribution in
`THIRD-PARTY.md` must be preserved.
