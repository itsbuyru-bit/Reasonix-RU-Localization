"""Проверки готового словаря translations/ru.json."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import common  # noqa: E402
import paths  # noqa: E402


class TestDictionary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ru = common.read_json(paths.RU_DICT, {})
        cls.source = common.read_json(paths.SOURCE, {})
        cls.rows = cls.source.get("rows", []) if cls.source else []

    def test_dictionary_exists(self):
        self.assertTrue(self.ru, "translations/ru.json отсутствует или пуст")

    def test_full_coverage(self):
        keys = {row["zh"] for row in self.rows}
        if not keys:
            self.skipTest("work/source.json is not generated; run scripts/extract_source.py")
        self.assertEqual(set(self.ru), keys)

    def test_no_empty_values(self):
        empty = [key for key, value in self.ru.items() if not value.strip()]
        self.assertEqual(empty, [])

    def test_placeholders(self):
        problems = []
        for key, value in self.ru.items():
            issues = common.placeholder_problems(key, value)
            if issues:
                problems.append((key, value, issues))
        self.assertEqual(problems, [])

    def test_no_chinese_left(self):
        import re

        cjk = re.compile(r"[\u4e00-\u9fff]")
        leftovers = [(key, value) for key, value in self.ru.items() if cjk.search(value)]
        self.assertEqual(leftovers, [])

    def test_key_terminology(self):
        self.assertEqual(self.ru.get("工作台"), "Верстак")
        self.assertEqual(self.ru.get("系统提示"), "Системный промпт")
        self.assertEqual(self.ru.get("{n} 个提示词"), "Промптов: {n}")
        self.assertEqual(self.ru.get("请求修改设置"), "Запрашивает изменение настройки")


class TestOverrides(unittest.TestCase):
    def test_overrides_are_valid(self):
        overrides = common.read_json(os.path.join(ROOT, "translations", "ru_overrides.json"), {})
        self.assertTrue(overrides)
        for key, value in overrides.items():
            self.assertTrue(value.strip(), key)
            self.assertEqual(common.placeholder_problems(key, value), [], key)


if __name__ == "__main__":
    unittest.main()
