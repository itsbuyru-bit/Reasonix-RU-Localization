import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import check_docs
import validate_language_pack


class TestLanguagePackValidation(unittest.TestCase):
    def test_ru_pack_is_valid(self):
        errors, warnings = validate_language_pack.validate_profile("ru-RU")
        self.assertEqual(errors, [])
        self.assertGreaterEqual(len(warnings), 0)

    def test_template_is_valid_with_partial(self):
        errors, warnings = validate_language_pack.validate_profile("_template", allow_partial=True)
        self.assertEqual(errors, [])

    def test_docs_links(self):
        self.assertEqual(check_docs.check(), [])


if __name__ == "__main__":
    unittest.main()
