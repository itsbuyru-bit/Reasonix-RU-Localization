# Contributing

Thank you for improving the Russian localization of Reasonix Studio. This
project is small and practical: every change should be reproducible, reversible,
and safe for the user's installation.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- **Fix a translation.** This is the most useful contribution.
- **Report a bug** in the patcher, the menu, or the update pipeline.
- **Improve documentation** or the troubleshooting guide.
- **Add a new language.** The pipeline is generic and BCP 47 based; see
  [docs/ADDING-A-LANGUAGE.md](docs/ADDING-A-LANGUAGE.md). Use the
  `languages/_template.json` and `locale/_template.json` templates, then run:
  ```bat
  python scriptsalidate_language_pack.py --lang de-DE
  python scripts\check_docs.py
  ```
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
or edit `locale/ru-RU.overrides.json` directly and open a pull request.
Include:

- the screen where the string appears;
- the Chinese source and/or English reference if you know it;
- the current Russian text;
- the suggested Russian text;
- confirmation that every `{placeholder}` is preserved.

For a one-off correction, add the key to `locale/ru-RU.overrides.json`, then:

```bat
py scripts\merge_parts.py --lang ru-RU --write
```

Do not edit `locale/ru-RU.json` by hand for a single fix: it is regenerated
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

## Submit a translation as a pull request

### New language

1. Fork the repository and create a branch:

   ```bat
   gh repo fork itsbuyru-bit/Reasonix-RU-Localization --clone
   cd Reasonix-RU-Localization
   git switch -c translation/de-DE
   ```

2. Copy the templates and set the BCP 47 profile:

   ```bat
   copy languages\_template.json languages\de-DE.json
   copy locale\_template.json locale\de-DE.json
   copy locale\_template.overrides.json locale\de-DE.overrides.json
   ```

   Set `code`, `base`, `aliases`, `display`, `global`, `dictionary`,
   `target_language` and `glossary`; translate `native` and `push`; then run
   `py scripts\build_native_patches.py --lang de-DE`.

3. Translate `locale\de-DE.json` (keep the Chinese keys and `{placeholders}`).

4. Validate and test:

   ```bat
   py scripts\validate_language_pack.py --lang de-DE
   py scripts\check_docs.py
   python -m unittest discover -s tests
   ```

5. Commit, push and open the PR:

   ```bat
   git add languages\de-DE.json locale\de-DE.json locale\de-DE.overrides.json
   git commit -m "translation: add German (de-DE)"
   git push -u origin translation/de-DE
   gh pr create --base main --head <your-user>:translation/de-DE ^
     --title "translation: add German (de-DE)" ^
     --body "Adds the BCP 47 de-DE language pack. Validator and docs checks pass."
   ```

   Add the `translation` label in the GitHub UI (or with
   `gh pr edit <number> --add-label translation`).

6. CI runs `Tests (Windows)`, including the language-pack validator and docs
   check. A maintainer reviews the pack and may add the `automerge` label.
   Auto-merge then waits for the required check; it never bypasses CI or branch
   protection.

### Fix an existing Russian string

1. Add the source key and the corrected value to
   `locale/ru-RU.overrides.json`.
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

4. Commit and open a PR with the `translation` label.

Do not edit `locale/ru-RU.json` by hand for a single correction: it is regenerated
from parts plus overrides.

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
