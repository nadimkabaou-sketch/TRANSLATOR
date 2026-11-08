import unittest
from pathlib import Path
from backend.core.pipeline import ScientificPipeline

class TestEndToEndPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = ScientificPipeline()

    def test_rsna_endometriosis_paper(self):
        sample_path = Path("samples/rsna_endometriosis_233482/article_233482.txt")
        self.assertTrue(sample_path.exists())

        result = self.pipeline.process_document(
            file_path=sample_path,
            domain="medicine_radiology"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["detected_language"]["code"], "en")
        self.assertEqual(result["target_language"], "fr")

        # QC Report checks
        qc = result["qc_report"]
        print(f"\n[RSNA End-to-End QC Report]: Overall Score = {qc['overall_score']}%, Rating = {qc['confidence_rating']}")
        print(f"Number fidelity: {qc['number_fidelity_pct']}%, Citation fidelity: {qc['citation_fidelity_pct']}%")
        
        self.assertGreaterEqual(qc["overall_score"], 95.0)
        self.assertGreaterEqual(qc["number_fidelity_pct"], 98.0)
        self.assertGreaterEqual(qc["citation_fidelity_pct"], 98.0)

        # Check export files generated
        exports = result["export_files"]
        for fmt in ["pdf", "docx", "latex", "txt", "html"]:
            self.assertIn(fmt, exports)
            self.assertTrue(Path(exports[fmt]).exists())
            print(f"Generated {fmt.upper()}: {exports[fmt]} ({Path(exports[fmt]).stat().st_size} bytes)")

    def test_physics_latex_paper(self):
        sample_path = Path("samples/physics/quantum_optics.tex")
        self.assertTrue(sample_path.exists())

        result = self.pipeline.process_document(
            file_path=sample_path,
            domain="physics_mathematics"
        )

        qc = result["qc_report"]
        print(f"\n[Physics LaTeX QC Report]: Overall Score = {qc['overall_score']}%, Rating = {qc['confidence_rating']}")
        self.assertGreaterEqual(qc["overall_score"], 90.0)

        # Verify Hamiltonian equation wasn't corrupted
        latex_out = Path(result["export_files"]["latex"]).read_text(encoding="utf-8")
        self.assertIn(r"\hbar \Delta_0 a^\dagger a", latex_out)

if __name__ == '__main__':
    unittest.main()
