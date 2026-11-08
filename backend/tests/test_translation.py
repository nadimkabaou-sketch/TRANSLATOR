import unittest
from backend.core.translator import ScientificTranslator

class TestTranslation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.translator = ScientificTranslator(device="cpu")

    def test_translate_endometriosis_sentence(self):
        sentence = "Endometriosis is a common condition impacting approximately 190 million individuals and up to 50% of women with infertility globally."
        res = self.translator.translate_segment(sentence, src_lang="en", domain="medicine_radiology")
        translated = res["translated"]
        print("\n[Test Translation Result]:", translated)
        
        # Verify numbers and percentages are 100% conserved
        self.assertIn("190", translated)
        self.assertIn("50%", translated)
        # Verify key medical terms translated accurately
        self.assertTrue("endométriose" in translated.lower() or "l'endométriose" in translated.lower())
        self.assertTrue("infertilité" in translated.lower())

    def test_translate_with_citations_and_mri(self):
        sentence = "Deep endometriosis in the pelvis was evaluated with MRI and transvaginal US [1, 2]."
        res = self.translator.translate_segment(sentence, src_lang="en", domain="medicine_radiology")
        translated = res["translated"]
        print("\n[Test MRI Translation Result]:", translated)
        
        # Verify citations and abbreviations
        self.assertIn("[1, 2]", translated)
        self.assertTrue("endométriose profonde" in translated.lower())
        self.assertTrue("irm" in translated.lower() or "mri" in translated.lower())

if __name__ == '__main__':
    unittest.main()
