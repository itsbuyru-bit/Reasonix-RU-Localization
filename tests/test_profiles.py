import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import common
import native_patches
import native_strings
import paths


class TestProfiles(unittest.TestCase):
    def test_ru_profile(self):
        profile = paths.load_profile("ru")
        self.assertEqual(profile["code"], "ru-RU")
        self.assertEqual(profile["display"], "Русский")
        self.assertEqual(profile["global"], "__RU_RU")
        self.assertEqual(profile["base"], "ru")
        self.assertEqual(profile["aliases"], ["ru"])
        self.assertTrue(os.path.isfile(paths.profile_dictionary(profile)))
        self.assertEqual(len(native_strings.patches(profile)), 8)

    def test_template_profile(self):
        profile = paths.load_profile("_template")
        self.assertEqual(profile["code"], "xx-XX")
        self.assertIn("native", profile)
        self.assertIn("push", profile)
        self.assertEqual(len(native_patches.build(profile)), 8)

    def test_template_dictionary(self):
        path = os.path.join(paths.TRANSLATIONS, "_template.json")
        self.assertTrue(os.path.isfile(path))
        data = common.read_json(path, {})
        self.assertEqual(len(data), 5201)
        self.assertGreaterEqual(len([v for v in data.values() if v]), 5100)

    def test_profiles_are_listed(self):
        codes = [profile["code"] for profile in paths.list_profiles()]
        self.assertIn("ru-RU", codes)
        self.assertNotIn("xx-XX", codes)


if __name__ == "__main__":
    unittest.main()
