"""Проверки патчей: якоря не пустые, замены реально меняют текст."""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import common  # noqa: E402
import inject_ru  # noqa: E402
import native_strings  # noqa: E402

CYRILLIC = re.compile(r"[А-Яа-яЁё]")


class TestWebPatches(unittest.TestCase):
    def test_each_replacement_changes_text(self):
        for name, old, new in inject_ru.patches():
            self.assertNotEqual(old, new, name)
            self.assertIn("ru", new, name)
            self.assertNotIn("ru", old, name)

    def test_anchor_shapes(self):
        names = [name for name, _, _ in inject_ru.patches()]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("R1_translate", names)
        self.assertIn("R5_machine", names)


class TestWebPatches252(unittest.TestCase):
    def test_252_replacements_change_text(self):
        for name, old, new in inject_ru.patches_252():
            self.assertNotEqual(old, new, name)
            self.assertIn("ru", new, name)
            self.assertNotIn("ru", old, name)

    def test_detect_i18n_layout(self):
        self.assertEqual(inject_ru.detect_i18n("var b={zh:{},en:{}};")[0], "b")
        self.assertEqual(inject_ru.detect_i18n("var v={zh:{},en:{}};")[0], "v")


class TestRunningGate(unittest.TestCase):
    def test_require_closed_refuses_while_running(self):
        from unittest.mock import patch

        with patch.object(inject_ru.paths, "app_running", return_value=True):
            with self.assertRaises(SystemExit):
                inject_ru.require_closed(False)
            inject_ru.require_closed(True)

    def test_require_closed_allows_when_stopped(self):
        from unittest.mock import patch

        with patch.object(inject_ru.paths, "app_running", return_value=False):
            inject_ru.require_closed(False)


class TestNativePatches(unittest.TestCase):
    def test_files_unique(self):
        files = [item["file"] for item in native_strings.PATCHES]
        self.assertEqual(len(files), len(set(files)))
        self.assertIn("uilang.js", files)
        self.assertIn("tray.js", files)

    def test_replacements_change_text(self):
        for item in native_strings.PATCHES:
            for tag, old, new in item["reps"]:
                self.assertTrue(old, (item["file"], tag))
                self.assertNotEqual(old, new, (item["file"], tag))
                # Либо языковая проверка, либо русский текст.
                self.assertTrue(
                    "ru" in new.lower() or CYRILLIC.search(new),
                    (item["file"], tag),
                )

    def test_no_cyrillic_mojibake(self):
        for item in native_strings.PATCHES:
            for tag, _old, new in item["reps"]:
                self.assertNotIn("Р\u00a0", new, (item["file"], tag))


class TestSettingsPatch(unittest.TestCase):
    def test_normal_append_uses_brackets(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "Settings.js")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("var Vl=[[`zh`,`中文`],[`en`,`英文`]];")
            text, changed = inject_ru.patch_settings(path, False)
            self.assertTrue(changed)
            self.assertIn("[`ru`,`Русский`]", text)
            self.assertIn("[`en`,`英文`],[`ru`,`Русский`]]", text)

    def test_broken_pair_is_repaired(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "Settings.js")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("var Vl=[[`zh`,`中文`],[`en`,`英文`],`ru`,`Русский`];")
            text, changed = inject_ru.patch_settings(path, False)
            self.assertTrue(changed)
            self.assertIn("[`ru`,`Русский`]]", text)
            self.assertNotIn(",`ru`,`Русский`]", text)


class TestPushPatches(unittest.TestCase):
    def test_push_patches(self):
        reps = inject_ru.push_patches()
        self.assertEqual(len(reps), 2)
        for name, old, new in reps:
            self.assertNotEqual(old, new, name)
            self.assertIn("ru", new.lower(), name)
        self.assertIn("На вашем компьютере", inject_ru.PUSH_TEXT_NEW)


class TestNeedsTranslation(unittest.TestCase):
    def test_chinese(self):
        self.assertTrue(common.needs_translation("重命名聊天"))

    def test_fullwidth_punctuation(self):
        self.assertTrue(common.needs_translation("Agent（{n}）"))

    def test_latin_passthrough(self):
        self.assertFalse(common.needs_translation("Token"))
        self.assertFalse(common.needs_translation("SearXNG"))

    def test_symbol_passthrough(self):
        self.assertFalse(common.needs_translation("…"))
        self.assertFalse(common.needs_translation("、"))


if __name__ == "__main__":
    unittest.main()
