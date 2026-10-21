"""Базовые проверки инструментов и извлечённого каталога."""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import common  # noqa: E402
import paths  # noqa: E402


class TestCommon(unittest.TestCase):
    def test_placeholders_ok(self):
        self.assertEqual(common.placeholder_problems("Привет, {name}!", "Привет, {name}!"), [])

    def test_placeholders_missing(self):
        problems = common.placeholder_problems("Файл {name} из {n}", "Файл из")
        self.assertTrue(problems)
        self.assertIn("{name}", " ".join(problems))

    def test_placeholders_extra(self):
        problems = common.placeholder_problems("Готово", "Готово, {n}")
        self.assertTrue(problems)

    def test_untranslated(self):
        self.assertTrue(common.looks_untranslated("重命名聊天", "重命名聊天"))
        self.assertTrue(common.looks_untranslated("重命名聊天", ""))
        self.assertFalse(common.looks_untranslated("重命名聊天", "Переименовать чат"))
        self.assertFalse(common.looks_untranslated("、", "、"))


class TestSourceCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = common.read_json(paths.SOURCE)
        if not cls.data:
            raise unittest.SkipTest(
                "work/source.json is not generated; run scripts/extract_source.py"
            )

    def test_catalog_exists(self):
        self.assertIsNotNone(self.data)

    def test_count_and_shape(self):
        rows = self.data["rows"]
        self.assertEqual(self.data["count"], len(rows))
        self.assertGreater(len(rows), 4000)
        for row in rows[:50]:
            self.assertIn("zh", row)
            self.assertIn("en", row)
            self.assertIn("fr", row)

    def test_keys_unique(self):
        rows = self.data["rows"]
        keys = [r["zh"] for r in rows]
        self.assertEqual(len(keys), len(set(keys)))

    def test_english_reference_coverage(self):
        rows = self.data["rows"]
        with_en = sum(1 for r in rows if r["en"])
        self.assertGreaterEqual(with_en, 4900)


if __name__ == "__main__":
    unittest.main()
