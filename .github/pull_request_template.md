## Summary

Describe the change and why it is needed.

## Type

- [ ] Bug fix
- [ ] Translation correction
- [ ] Documentation
- [ ] Tooling / tests
- [ ] New feature

## Verification

- [ ] `python -m unittest discover -s tests`
- [ ] `node --check scripts/extract_bundle.mjs` and the other Node helpers
- [ ] `py scripts/inject_ru.py --dry-run` (if anchors changed)
- [ ] `py scripts/patch_asar_ru.py --dry-run` (if native strings changed)
- [ ] Tested on Reasonix Studio version: ...

## Screenshots

Add before/after screenshots for visible UI changes.

## Checklist

- [ ] No API keys, tokens, session data, private code, or `app.asar` included.
- [ ] Every `{placeholder}` is preserved.
- [ ] Anchors still match exactly once.
- [ ] `README.md` and `README.ru.md` updated for behavior changes.
- [ ] `CHANGELOG.md` updated.
- [ ] The change is licensed under MIT and preserves the French toolkit attribution.
