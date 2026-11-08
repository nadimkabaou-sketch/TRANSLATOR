import unittest
from backend.core.entity_protector import EntityProtector

class TestEntityProtector(unittest.TestCase):
    def setUp(self):
        self.protector = EntityProtector()

    def test_protect_and_restore_math(self):
        text = "The energy is given by $E = mc^2$ and the integral is $\\int_0^\\infty e^{-x} dx = 1$."
        prot, p_map = self.protector.protect(text)
        self.assertIn("<x", prot)
        restored, warnings = self.protector.restore(prot, p_map)
        self.assertEqual(restored, text)
        self.assertEqual(len(warnings), 0)

    def test_protect_and_restore_citations_and_measures(self):
        text = "Deep endometriosis was found in 42.5% of cases [1, 3-5], with a mean lesion size of 15.4 mm at 3.0 T MRI."
        prot, p_map = self.protector.protect(text)
        # Check that 42.5%, [1, 3-5], 15.4 mm, 3.0 T were replaced
        self.assertNotIn("42.5%", prot)
        self.assertNotIn("[1, 3-5]", prot)
        self.assertNotIn("15.4 mm", prot)
        self.assertNotIn("3.0 T", prot)
        
        restored, warnings = self.protector.restore(prot, p_map)
        self.assertEqual(restored, text)
        self.assertEqual(len(warnings), 0)

    def test_doi_and_url_protection(self):
        text = "Available online at https://pubs.rsna.org/doi/10.1148/radiol.233482 with DOI 10.1148/radiol.233482."
        prot, p_map = self.protector.protect(text)
        restored, warnings = self.protector.restore(prot, p_map)
        self.assertEqual(restored, text)
        self.assertEqual(len(warnings), 0)

if __name__ == '__main__':
    unittest.main()
