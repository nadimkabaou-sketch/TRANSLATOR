import unittest
from backend.core.quality_controller import QualityController

class TestQualityController(unittest.TestCase):
    def setUp(self):
        self.qc = QualityController()

    def test_perfect_alignment(self):
        src = [
            {"id": "elem_0", "type": "paragraph", "text": "Endometriosis affects 190 million women worldwide [1]."},
            {"id": "elem_1", "type": "paragraph", "text": "MRI with 3.0 T improves diagnosis with p < 0.05."}
        ]
        trg = [
            {"id": "elem_0", "type": "paragraph", "text": "L'endométriose touche 190 millions de femmes dans le monde [1]."},
            {"id": "elem_1", "type": "paragraph", "text": "L'IRM avec 3.0 T améliore le diagnostic avec p < 0.05."}
        ]
        report = self.qc.audit_document(src, trg)
        self.assertGreaterEqual(report["overall_score"], 98.0)
        self.assertEqual(report["confidence_rating"], "HIGH")
        self.assertFalse(report["requires_human_review"])

    def test_detect_missing_number_and_citation(self):
        src = [
            {"id": "elem_0", "type": "paragraph", "text": "A total of 45 patients responded out of 100 [1, 2]."}
        ]
        # In this corrupt translation, the number 45 and citation [1, 2] were dropped
        trg = [
            {"id": "elem_0", "type": "paragraph", "text": "Un groupe de patients a répondu sur 100."}
        ]
        report = self.qc.audit_document(src, trg)
        self.assertLess(report["overall_score"], 90.0)
        self.assertTrue(report["requires_human_review"])
        self.assertGreater(len(report["issues"]), 0)
        issue_msgs = [i["message"] for i in report["issues"]]
        self.assertTrue(any("45" in m for m in issue_msgs))
        self.assertTrue(any("citations" in m for m in issue_msgs))

if __name__ == '__main__':
    unittest.main()
