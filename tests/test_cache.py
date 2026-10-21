"""Проверка безопасного сброса кэша: настройки и localStorage не трогаются."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import clear_cache  # noqa: E402


class TestClearCache(unittest.TestCase):
    def test_removes_only_cache_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            for folder in ("Cache", "Code Cache", "GPUCache"):
                os.makedirs(os.path.join(tmp, folder))
                with open(os.path.join(tmp, folder, "blob"), "w", encoding="utf-8") as handle:
                    handle.write("cache")
            keep = ("Local Storage", "Session Storage", "Network", "Preferences")
            for folder in keep:
                os.makedirs(os.path.join(tmp, folder))
                with open(os.path.join(tmp, folder, "keep"), "w", encoding="utf-8") as handle:
                    handle.write("keep")

            removed = clear_cache.clear_profile(tmp)
            self.assertGreaterEqual(len(removed), 3)
            for folder in ("Cache", "Code Cache", "GPUCache"):
                self.assertFalse(os.path.exists(os.path.join(tmp, folder)))
            for folder in keep:
                self.assertTrue(os.path.exists(os.path.join(tmp, folder)))


if __name__ == "__main__":
    unittest.main()
