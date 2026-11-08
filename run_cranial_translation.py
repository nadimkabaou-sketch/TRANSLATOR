import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.pipeline import ScientificPipeline

def main():
    target_pdf = Path(r"C:\Users\Kabaou\Downloads\Nouveau dossier (7)\13244_2019_Article_719.pdf")
    if not target_pdf.exists():
        print(f"Error: Target file not found at {target_pdf}")
        sys.exit(1)

    print(f"=== Translation Pipeline Launch ===")
    print(f"Target: {target_pdf.name} ({target_pdf.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Domain: medicine_radiology (Neuroradiology & Cranial Nerves)")
    print(f"Target language: French (fr)")
    print("-" * 50)

    start_time = time.time()
    pipeline = ScientificPipeline()

    def on_progress(stage: str, percent: int):
        elapsed = time.time() - start_time
        print(f"[{elapsed:6.1f}s] [{percent:3d}%] {stage}")

    result = pipeline.process_document(
        file_path=target_pdf,
        domain="medicine_radiology",
        progress_callback=on_progress
    )

    total_time = time.time() - start_time
    print("-" * 50)
    print(f"=== Translation Completed in {total_time:.1f}s ===")
    print(f"Source Language: {result['detected_language']['name']} ({result['detected_language']['code']})")
    print(f"Target Language: {result['target_language']}")
    
    qc = result["qc_report"]
    print(f"QC Overall Score: {qc['overall_score']}% ({qc['confidence_rating']})")
    print(f"Numbers Fidelity: {qc['number_fidelity_pct']}% | Citations Fidelity: {qc['citation_fidelity_pct']}%")
    print(f"Total Elements: {qc['total_elements']} (Perfect: {qc['perfect_elements']})")
    
    print("\nGenerated Output Files:")
    for fmt, p in result["export_files"].items():
        size_kb = Path(p).stat().st_size / 1024
        print(f"  - [{fmt.upper()}] {p} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
