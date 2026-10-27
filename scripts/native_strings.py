"""Нативные патчи Reasonix Studio из языкового профиля.

Русские блоки лежат в languages/ru.json (`native_patches`). Если профиль
нового языка содержит только простые поля `native`, блоки собирает
native_patches.build() — писать Python для нового языка не нужно.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths


def patches(profile):
    data = profile.get("native_patches")
    if data:
        return data
    import native_patches

    return native_patches.build(profile)


PATCHES = patches(paths.load_profile(paths.DEFAULT_LANG))
